import os
from log import LogEvent
from .basicCrawler import BasicCrawler, BasicCrawlerTask

import time

class FileCrawlTask(BasicCrawlerTask):

    def __init__(self, url, log_queue, last_task=False):
        """ Constructor method
        """
        super().__init__(url, last_task=last_task)
        if url:
            self.log_queue = log_queue
            
    def run(self):
        self.log_queue.put(LogEvent("INFO", __name__, "Gonna start to crawl %s" % self.url))

        content = ""
        status = "data"
        
        try:
            f = open(self.url, "r")
            content = f.read()
            f.close()
        except Exception as e:
            em = f"ERROR for {self.url}\n{e}"
            self.log_queue.put(LogEvent("ERROR", __name__, em))
            status = "error"
            content = em
        
        return {"status": status, "url": self.url, "content": content, "timestamp": str(time.time()).split('.')[0]}


class FileCrawler(BasicCrawler):
    
    def __init__(self, number_processes, result_queue, log_queue, dead_pill,
                 directory, mode):
        """ Constructor method
        """
        super().__init__(number_processes, result_queue, log_queue, dead_pill, mode)  
        self.tasks = 0
        self._fill_crawling_tasks(directory)

    def _fill_crawling_tasks(self, directory):

        self.log_queue.put(LogEvent("INFO", __name__, "Fill File Crawler with tasks"))


        for file_name in os.listdir(directory):
            if self.mode == "DEBUG" and self.tasks > 15: break 
            crawler_task = FileCrawlTask(os.path.join(directory, file_name), self.log_queue)
            self.crawling_tasks.put(crawler_task)
            self.tasks += 1

        crawler_task = FileCrawlTask("", self.log_queue, last_task=True)
        self.crawling_tasks.put(crawler_task)
