from crawler import CommonCrawlCrawlerFromSQL, CommonCrawlCrawler, DynamicCrawler, FileCrawler
from checker import BasicChecker
from log import Logger, LogEvent
from datetime import datetime
import argparse
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
import multiprocessing
from os import path, mkdir
import yaml
import signal
import sys
import time

from database import get_session, create_database, create_my_engine
from database import CheckerResult, CheckerRule 
from checker import rules

CONFIG_FILE = "./config.yml"
DEAD_PILL = "DEADPILL"

def main():
    # Handle arguments
    parser = argparse.ArgumentParser(description='Crawl websites and check some rules.')
    parser.add_argument('--module', help='Crawling module [common_crawl, common_crawl_sql, file, dynamic]')
    parser.add_argument('--urls', help='Path to a list of URL you want to crawl')
    parser.add_argument('--config', help='Path to the config file')
    parser.add_argument('--files', help='Path to a file containing commonCrawl information')
    parser.add_argument('--crawl', help='The crawl id if the CC data are selected from a database')
    args = parser.parse_args()

    # Handle processes
    
    # start time to calc runtime duration 
    start_time = time.time()
    global CONFIG_FILE
    print(CONFIG_FILE)
    if args.config:
        CONFIG_FILE = args.config

    with open(CONFIG_FILE, "r") as ymlfile:
        config = yaml.load(ymlfile, Loader=yaml.FullLoader)

    if not config:
        print(f"No such config: { CONFIG_FILE }")
        return 1

    
    output_dir = config["general"]["output"]
    if path.exists(output_dir) == False:
        mkdir(output_dir)

    timestamp = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")

    # Init logger
    log_level = config["general"]["log_level"]
    log_queue = multiprocessing.Manager().Queue()
    log_file = path.join(output_dir, f"{timestamp}.log")
    logger = Logger(log_queue, log_level, log_file, DEAD_PILL)
    log_process = multiprocessing.Process(target=logger.run)
    log_process.start()

    # Init database
    applied_rules = config["checker"]["rules"] or []  
    create_database()
    database_session = get_session() 

    for rule_name in applied_rules:
        rule = getattr(rules, rule_name)
        if not rule: 
            # dont forget to load rule in __init__
            raise Exception(f"No such rule {rule_name}")

        rule_exists = database_session.query(CheckerRule) \
            .filter(CheckerRule.name == rule_name).first()
        if rule_exists:
            continue
        
        checker_rule = CheckerRule(
                name = rule_name,
                name_informal = rule.name_informal.strip(),
                description = rule.description.strip()
                )
        database_session.add(checker_rule)

    database_session.commit()
    database_session.close()

    # Init Crawler and Checker 
    number_crawler_processes = int(config["general"]["number_crawler_processes"])
    number_checker_processes = int(config["general"]["number_checker_processes"])
    mode = config["general"]["mode"] 

    if args.urls:
        urls = args.urls
    else:
        urls = config["crawler"]["urls"] or []

    if args.files:
        files = args.files
    else:
        files = config["crawler"]["files"] or []

    db_file = config["crawler"]["db_path"] or []

    crawl = args.crawl if args.crawl else ""
    module = args.module if args.module else ""

    result_queue = multiprocessing.Queue()

    if module == "common_crawl_sql":
        currentCrawler = CommonCrawlCrawlerFromSQL(number_crawler_processes, result_queue,
                            log_queue, DEAD_PILL, db_file, crawl, mode)
    if module == "common_crawl":
        currentCrawler = CommonCrawlCrawler(number_crawler_processes, result_queue,
                            log_queue, DEAD_PILL, urls, files, mode)    
    elif module == "dynamic":
        currentCrawler = DynamicCrawler(number_crawler_processes, result_queue,
                            log_queue, DEAD_PILL, urls, mode)
    elif module == "file":
        currentCrawler = FileCrawler(number_crawler_processes, result_queue,
                            log_queue, DEAD_PILL, files[0], mode)


    basicChecker = BasicChecker(number_checker_processes, result_queue, log_queue,
                            DEAD_PILL, applied_rules, mode)

    # start checker process
    checker_process = multiprocessing.Process(target=basicChecker.run)
    checker_process.start()

    # handler to exit
    def exit_handler(sig, frame):
        log_queue.put(LogEvent("INFO", __name__, "You pressed Ctrl+C"))
        checker_process.terminate()
        checker_process.join()
        sys.exit(0)

    signal.signal(signal.SIGINT, exit_handler)
    signal.signal(signal.SIGTERM, exit_handler)

    # start crawler
    currentCrawler.run()

    # shutdown program
    checker_process.join()

    delta_time = round(time.time() - start_time)
    log_queue.put(LogEvent("INFO", __name__, f"Execution Time: {delta_time} seconds"))

    log_queue.put(DEAD_PILL)
    log_process.join()

if __name__ == '__main__':
    multiprocessing.set_start_method('spawn')
    main()
