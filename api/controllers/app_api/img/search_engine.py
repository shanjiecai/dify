import random
import time
from urllib.parse import urlparse

from icrawler import Feeder, ImageDownloader
from icrawler.builtin import BaiduImageCrawler, BingImageCrawler, Filter

from mylogger import logger


class MyImageDownloader(ImageDownloader):
    # def __init__(self, *args, **kwargs):
    #     super(MyImageDownloader).__init__(*args, **kwargs)
    #     # self.filename_prefix = kwargs.get('filename_prefix', '')
    #     # self.filename = kwargs.get('filename', '')
    def __init__(self, thread_num, signal, session, storage):
        super().__init__(thread_num, signal, session, storage)
        self.fetched_num = 0
        self.filenames = []

    def get_filename(self, task, default_ext="jpg"):
        url_path = urlparse(task['file_url'])[2]
        if '.' in url_path:
            extension = url_path.split('.')[-1]
            if extension.lower() not in [
                'jpg', 'jpeg', 'png', 'bmp', 'tiff', 'gif', 'ppm', 'pgm'
            ]:
                extension = default_ext
        else:
            extension = default_ext
        # works for python3
        # filename = base64.b64encode(url_path.encode()).decode()
        # if self.filename:
        #     filename = self.filename
        # else:
        #     filename = url_path.split('/')[-1]
        # if self.filename_prefix:
        #     filename = self.filename_prefix + '_' + filename
        filename = url_path.split('/')[-1].split('.')[0]
        print(filename)
        return '{}.{}'.format(filename, extension)

    def download(self, task, default_ext, timeout=5, max_retry=3, overwrite=False, **kwargs):
        """Download the image and save it to the corresponding path.

        Args:
            task (dict): The task dict got from ``task_queue``.
            timeout (int): Timeout of making requests for downloading images.
            max_retry (int): the max retry times if the request fails.
            **kwargs: reserved arguments for overriding.
        """
        file_url = task["file_url"]
        task["success"] = False
        task["filename"] = None
        retry = max_retry

        if not overwrite:
            with self.lock:
                self.fetched_num += 1
                filename = self.get_filename(task, default_ext)
                if self.storage.exists(filename):
                    self.logger.info("skip downloading file %s", filename)
                    return
                self.fetched_num -= 1

        while retry > 0 and not self.signal.get("reach_max_num"):
            try:
                response = self.session.get(file_url, timeout=timeout)
            except Exception as e:
                self.logger.error(
                    "Exception caught when downloading file %s, " "error: %s, remaining retry times: %d",
                    file_url,
                    e,
                    retry - 1,
                )
            else:
                if self.reach_max_num():
                    self.signal.set(reach_max_num=True)
                    break
                elif response.status_code != 200:
                    self.logger.error("Response status code %d, file %s", response.status_code, file_url)
                    break
                elif not self.keep_file(task, response, **kwargs):
                    break
                with self.lock:
                    self.fetched_num += 1
                    filename = self.get_filename(task, default_ext)
                    self.filenames.append(filename)
                self.logger.info("image #%s\t%s", self.fetched_num, file_url)
                self.storage.write(filename, response.content)
                task["success"] = True
                task["filename"] = filename
                print(f"download {file_url} success")
                break
            finally:
                retry -= 1


class MyBingFeed(Feeder):
    def get_filter(self):
        search_filter = Filter()

        # type filter
        def format_type(img_type):
            prefix = "+filterui:photo-"
            return prefix + "animatedgif" if img_type == "animated" else prefix + img_type

        type_choices = ["photo", "clipart", "linedrawing", "transparent", "animated"]
        search_filter.add_rule("type", format_type, type_choices)

        # color filter
        def format_color(color):
            prefix = "+filterui:color2-"
            if color == "color":
                return prefix + "color"
            elif color == "blackandwhite":
                return prefix + "bw"
            else:
                return prefix + "FGcls_" + color.upper()

        color_choices = [
            "color",
            "blackandwhite",
            "red",
            "orange",
            "yellow",
            "green",
            "teal",
            "blue",
            "purple",
            "pink",
            "white",
            "gray",
            "black",
            "brown",
        ]
        search_filter.add_rule("color", format_color, color_choices)

        # size filter
        def format_size(size):
            if size in ["large", "medium", "small"]:
                return "+filterui:imagesize-" + size
            elif size == "extralarge":
                return "+filterui:imagesize-wallpaper"
            elif size.startswith(">"):
                wh = size[1:].split("x")
                assert len(wh) == 2
                return "+filterui:imagesize-custom_{}_{}".format(*wh)
            else:
                raise ValueError(
                    'filter option "size" must be one of the following: '
                    "extralarge, large, medium, small, >[]x[] "
                    "([] is an integer)"
                )

        search_filter.add_rule("size", format_size)

        # licence filter
        license_code = {
            "creativecommons": "licenseType-Any",
            "publicdomain": "license-L1",
            "noncommercial": "license-L2_L3_L4_L5_L6_L7",
            "commercial": "license-L2_L3_L4",
            "noncommercial,modify": "license-L2_L3_L5_L6",
            "commercial,modify": "license-L2_L3",
        }

        def format_license(license):
            return "+filterui:" + license_code[license]

        license_choices = list(license_code.keys())
        search_filter.add_rule("license", format_license, license_choices)

        # layout filter
        layout_choices = ["square", "wide", "tall"]
        search_filter.add_rule("layout", lambda x: "+filterui:aspect-" + x, layout_choices)

        # people filter
        people_choices = ["face", "portrait"]
        search_filter.add_rule("people", lambda x: "+filterui:face-" + x, people_choices)

        # date filter
        date_minutes = {"pastday": 1440, "pastweek": 10080, "pastmonth": 43200, "pastyear": 525600}

        def format_date(date):
            return "+filterui:age-lt" + str(date_minutes[date])

        date_choices = list(date_minutes.keys())
        search_filter.add_rule("date", format_date, date_choices)
        # print(search_filter)
        return search_filter

    def feed(self, keyword, offset, max_num, filters=None):
        base_url = "https://www.bing.com/images/async?q={}&first={}"
        self.filter = self.get_filter()
        filter_str = self.filter.apply(filters)
        filter_str = "&qft=" + filter_str if filter_str else ""

        # for i in range(offset, offset + max_num, 20):
        #     url = base_url.format(keyword, i) + filter_str
        #     print(url)
        #     self.out_queue.put(url)
        #     self.logger.debug(f"put url to url_queue: {url}")
        # 改为随机获取
        url = base_url.format(keyword, random.randint(0, 20)) + filter_str
        print(url)
        self.out_queue.put(url)
        self.logger.debug(f"put url to url_queue: {url}")


class MyBaiduFeeder(Feeder):
    def get_filter(self):
        search_filter = Filter()

        # type filter
        type_code = {
            "portrait": "s=3&lm=0&st=-1&face=0",
            "face": "s=0&lm=0&st=-1&face=1",
            "clipart": "s=0&lm=0&st=1&face=0",
            "linedrawing": "s=0&lm=0&st=2&face=0",
            "animated": "s=0&lm=6&st=-1&face=0",
            "static": "s=0&lm=7&st=-1&face=0",
        }

        def format_type(img_type):
            return type_code[img_type]

        type_choices = list(type_code.keys())
        search_filter.add_rule("type", format_type, type_choices)

        # color filter
        color_code = {
            "red": 1,
            "orange": 256,
            "yellow": 2,
            "green": 4,
            "purple": 32,
            "pink": 64,
            "teal": 8,
            "blue": 16,
            "brown": 12,
            "white": 1024,
            "black": 512,
            "blackandwhite": 2048,
        }

        def format_color(color):
            return f"ic={color_code[color]}"

        color_choices = list(color_code.keys())
        search_filter.add_rule("color", format_color, color_choices)

        # size filter
        def format_size(size):
            if size in ["extralarge", "large", "medium", "small"]:
                size_code = {"extralarge": 9, "large": 3, "medium": 2, "small": 1}
                return f"z={size_code[size]}"
            elif size.startswith("="):
                wh = size[1:].split("x")
                assert len(wh) == 2
                return "width={}&height={}".format(*wh)
            else:
                raise ValueError(
                    'filter option "size" must be one of the following: '
                    "extralarge, large, medium, small, >[]x[] "
                    "([] is an integer)"
                )

        search_filter.add_rule("size", format_size)

        return search_filter

    def feed(self, keyword, offset, max_num, filters=None):
        base_url = "http://image.baidu.com/search/acjson?tn=resultjson_com" "&ipn=rj&word={}&pn={}&rn=30"
        self.filter = self.get_filter()
        filter_str = self.filter.apply(filters, sep="&")
        # for i in range(offset, offset + max_num, 30):
        #     url = base_url.format(keyword, i)
        #     if filter_str:
        #         url += "&" + filter_str
        #     self.out_queue.put(url)
        #     self.logger.debug(f"put url to url_queue: {url}")
        # 改为随机获取
        url = base_url.format(keyword, random.randint(0, 30))
        if filter_str:
            url += "&" + filter_str
        print(url)
        self.out_queue.put(url)
        self.logger.debug(f"put url to url_queue: {url}")


def search_engine_invoke(keyword, shape=None, size=None, dst_dir="./", max_num=1) -> list[str]:
    # Initialize Bing crawler
    bing_crawler = BingImageCrawler(storage={'root_dir': dst_dir},
                                    downloader_cls=MyImageDownloader,
                                    feeder_cls=MyBingFeed,
                                    downloader_threads=4,
                                    parser_threads=2
                                    )

    try:
        # Try crawling with Bing
        # layout_choice = ["square", "wide", "tall"]
        if shape:
            if shape=="square":
                layout = "square"
            elif shape=="vertical":
                layout = "tall"
            elif shape=="horizontal":
                layout = "wide"
            else:
                layout = "tall"
        else:
            layout = "tall"
        begin = time.time()
        bing_filters = {
            # 'license': 'commercial,modify',
            'layout': layout,
            # 'type': 'photo',
        }
        bing_crawler.crawl(keyword=keyword, max_num=max_num, overwrite=True,
                           filters=bing_filters
                           )

        logger.info(f"搜索引擎耗时：{time.time() - begin}")
        return bing_crawler.downloader.filenames
    except Exception as e:
        # print("Error occurred with Bing:", e)
        # print("Retrying with Baidu...")
        logger.info(f"Error occurred with Bing: {e}")
        # Initialize Baidu crawler
        baidu_crawler = BaiduImageCrawler(storage={'root_dir': dst_dir},
                                          downloader_cls=MyImageDownloader,
                                          feeder_cls=MyBaiduFeeder,
                                          downloader_threads=2,
                                          parser_threads=2,
                                          )

        try:
            # Try crawling with Bing
            baidu_filter = {
                'type': 'static'
            }
            baidu_crawler.crawl(keyword=keyword, max_num=max_num, overwrite=True,
                                filters=baidu_filter
                                )
            return baidu_crawler.downloader.filenames
        except Exception as e:
            # print("Error occurred with Baidu:", e)
            # print("Both Bing and Baidu failed to fetch images.")
            logger.info(f"Error occurred with Baidu: {e}")


if __name__ == '__main__':
    print(search_engine_invoke("run", max_num=3))
