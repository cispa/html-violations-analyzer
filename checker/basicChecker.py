from multiprocessing import Pool, get_context
from log import LogEvent
from checker import rules
import signal
from datetime import datetime
from urllib.parse import urlparse
from hashlib import md5

from database import CheckerResult, Website, CheckerRule, get_session, create_my_engine

class BasicChecker:
    """ Takes results from the result queue and checks the specified rules.
        If the result queue outputs the dead pill, the checker shuts down.

        :param number_processes: The maximum number of checker processes
        :type number_processes: int
        :param result_queue: The queue that outputs the crawler results
        :type result_queue: multiprocessing.Queue
        :param log_queue: The queue that takes log events
        :type log_queue: multiprocessing.Manager().Queue
        :param dead_pill: The dead pill to shutdown the checker
        :type dead_pill: string
        :param rules: The name of rules to apply
        :type rules: list
        :param mode: The current running mode, debug or prod
        :type mode: string
        :param database_engine: The path to the sqlite database TODO
        :type database_file: string
    """

    def __init__(self, number_processes, result_queue, log_queue, dead_pill,
                 rules, mode):
        """ Constructor method
        """
        self.number_processes = number_processes
        self.result_queue = result_queue
        self.log_queue = log_queue
        self.dead_pill = dead_pill
        self.rules = rules
        self.mode = mode
        signal.signal(signal.SIGINT, signal.SIG_IGN)

    def _handle_error(self, e):
        """ Error handler
        """
        self.log_queue.put(LogEvent("ERROR", __name__, e))

    def run(self):
        """ The function 'run' is started in a new process to handle log events
            from the log queue
        """
        pool = get_context("spawn").Pool(self.number_processes)

        while 1:
            self.log_queue.put(LogEvent("INFO", __name__, f"SIZE: {self.result_queue.qsize()}"))

            self.log_queue.put(LogEvent("DEBUG", __name__, "Checker is running"))
            requestResult = self.result_queue.get()
            if requestResult == self.dead_pill: 
                self.log_queue.put(LogEvent("DEBUG", __name__, "Shutdown Checker"))
                # pool.terminate()
                break

            try:
                pool.starmap_async(
                    check,
                    [(self.rules, requestResult, self.log_queue)],
                    error_callback=self._handle_error
                )
            except Exception as e:
                self.log_queue.put(LogEvent("ERROR", __name__, f"Checker failed to put job in queue: {e}"))
                # break ?

        pool.close()
        pool.join()

def check(rule_names, result, log_queue):
    """ The function 'check' is called by the BasicChecker.
        It checks all defined rules for one crawler result.
        :param rule_names: A list of rules that are applied
        :type rule_names: list
        :param result: The request result that is checked
        :type result: dict 
        :param log_queue: The queue that takes log events
        :type log_queue: multiprocessing.Manager().Queue
    """
    
    database_session = get_session() 
    url = urlparse(result['url'])
    content_hash = md5(result["content"].encode()).hexdigest()

    crawl_id = result["crawl_id"] if "crawl_id" in result else "TBD"
    tranco_rank = result["tranco_rank"] if "tranco_rank" in result else -1

    # Dirty quick db fix
    # If an error occures, the connection stayed open...
    try:
        # Logging an error case
        if result["status"] == "error":            
            website = Website(
                    hostname=url.hostname,
                    domain=result["domain"],
                    path=url.path,
                    country=url.hostname.split('.')[-1] if url.hostname else "",
                    content="",
                    content_hash=content_hash,
                    size=len(result['content']),
                    category="TBD",
                    extra_info=crawl_id,
                    crawl=crawl_id,
                    tranco_rank=tranco_rank,
                    error=result["content"],
                    timestamp=datetime.fromtimestamp(int(result["timestamp"]))
                    )
            database_session.add(website)
            database_session.commit()
            database_session.close()
            del website
            return

        checker_results = []

        # Starting to check
        worked = 0
        for rule_name in rule_names:
            """
            log_queue.put(LogEvent(
                "DEBUG", __name__, f"Working on {rule_name} with {url.geturl()}"
            ))
            """
            try:
                rule = getattr(rules, rule_name)
            except:
                log_queue.put(LogEvent(
                    "ERROR", __name__, f"Skip {rule_name}. No such rule exists."
                ))
                continue

            try:
                res = rule.run_rule(result["content"])
            except Exception as e:
                log_queue.put(LogEvent(
                    "ERROR", __name__, f"Rule {rule_name} failed: {e}"
                ))
                continue

            del rule

            if res == True:
                line = f"{url.geturl()} {rule_name} works ✓"
                worked += 1
            else:
                line = f"{url.geturl()} {rule_name} fail X"

            # log_queue.put(LogEvent("DEBUG", __name__, line))
            # f = open('result.txt', 'a+')
            # f.write(line + "\n")
            # f.close()
            checker_results.append((rule_name, res))

        log_queue.put(LogEvent("DEBUG", __name__, f"{url.geturl()} worked {worked}/{len(rule_names)}"))

        # Storing website infos
        # TODO add more
        website = Website(
                hostname=url.hostname,
                domain=result["domain"],
                path=url.path,
                country=url.hostname.split('.')[-1] if url.hostname else "",
                content="", #  add only if check fails
                content_hash=content_hash,
                size=len(result['content']),
                category="TBD",
                extra_info=crawl_id,
                crawl=crawl_id,
                tranco_rank=tranco_rank,
                timestamp=datetime.fromtimestamp(int(result["timestamp"]))
                )
        database_session.add(website)

        for rule_name, res in checker_results:
            rule_object = database_session.query(CheckerRule) \
                .filter(CheckerRule.name == rule_name).first()

            if res == False and website.content == "":
                website.content = result["content"]

            database_session.add(CheckerResult(
                    rule_id = rule_object.id,
                    website_id = website.id,
                    result = res))

        database_session.commit()
    except Exception as e:
        log_queue.put(LogEvent("INFO", __name__, f"ERROR in chekcer: {e}"))

    database_session.close()

    del checker_results
    del website
