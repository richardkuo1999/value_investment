from utils.utils import fetch_webpage

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/97.0.4692.99 Safari/537.36",
    "Cookie": "CLIENT%5FID=20241210210956023%5F111%2E255%2E220%2E131; IS_TOUCH_DEVICE=F; SCREEN_SIZE=WIDTH=1710&HEIGHT=1112; TW_STOCK_BROWSE_LIST=2330; _ga=GA1.1.812880287.1733836199; _cc_id=28e3f970dec12837e20c15307c56ec28; panoramaId_expiry=1734441000958; panoramaId=cc21caa7184af9f0e6c620d0a8f8185ca02cc713f5ac9a4263f82337f1b4a2b7; panoramaIdType=panoDevice; __gads=ID=b2e3ed3af73d1ae3:T=1733836201:RT=1733922308:S=ALNI_Mb7ThRkzKYSy21PA-6lcXT9vRc3Kg; __gpi=UID=00000f896331f355:T=1733836201:RT=1733922308:S=ALNI_MZqCnVGqHlRq9KdKeQAuDHF4Gjfxw; __eoi=ID=f9846d25b9e203d1:T=1733836201:RT=1733922308:S=AA-AfjY-BVqunx2hOWeWbgCq5_UI; cto_bundle=Lk53dF84ZDdteU1aenVEZW9WZklPTG5FYU9MdDRjOFQ5NkVoZ1lYOTVnMzNVTFFDOUFNYXZyWjBmSndHemVhOFdhQTlMZHJUNCUyQiUyRm9RSlJpd0FBUXlYd2NDQmdXRkh0ZkM1SUY1VHM2b2NQc0ljcVJGSTFwY3RPRmI1WEwxRXBMTVUzUDgxWjBLSUVjOSUyQk1veUdMcFZjRDlsNVElM0QlM0Q; cto_bundle=4XBCG184ZDdteU1aenVEZW9WZklPTG5FYU9NcXlSZm1lU2RKOGgwaHlUM1RzWXU5QWMlMkJuR1lkb25qSjdRYUxHWWhsUEhMRGxCeHVuUVF6WGlGTkxjbVNuYmFqbERVRm11QjlTR0xBckVvdmE2ZlJFQmhQdURma3lnRHNjM25xOFpNNEg4WWZLc0wxZVN6c1lEUFZDM3VvNnlxdWFGV2FiNThNRSUyRlZ4N3ZxakZzT3I0cEclMkZYdm1NN2RQNSUyRlBUM1FQJTJCSE80YUxVVDlKUUFLblZuMllUZVBzaVdFZyUzRCUzRA; cto_bidid=NK15uF9ZWnQ2aGIwVGNqRUFJRGgxVUVSejh0b1dEczFNU0FJTmR1RVl5SnljdDVmY08xc1NndnRUZXZMYmVvJTJCMVNya2R5RVk1QWpEeiUyQnBsJTJCOUZJQTBWJTJGcGhTcWFvUGs1QkxuUCUyQnVjUU42MXZIQWxSb2xsVVFrNml2T2g0TG1NcHphS0I4YzdzQXVRVXpRSXlCZU1VV1M4SDN3JTNEJTNE; FCNEC=%5B%5B%22AKsRol-AsNGK3J633zneXVvjb6XxOsqQYrBvxCwcMi0GME-2BDMLBX3LEYQ83Li8Hw71LSdsgNxpfHUX3Nw3FGDMDQhm3wUeXgalEarK4zql1IO51tBobJmU-o44Bd5tOC0OcT6RNUf2w8Bl6YsQ6f2yA7JoK-Uwlw%3D%3D%22%5D%5D; _ga_0LP5MLQS7E=GS1.1.1733921765.2.1.1733922576.51.0.0",
}


class Goodinfo:
    def __init__(self, stock_id: str) -> None:
        self.stock_id = stock_id
        self.TTMPEG = self.get_peg()
        self.CompanyINFO = self.get_company_info()

    def get_peg(self) -> str | None:
        """
        Get PEG ratio from Goodinfo website for given stock ID
        Args:
            stock_id: Stock ID to lookup
        Returns:
            PEG ratio as string if found, None otherwise
        """
        url = f"https://goodinfo.tw/tw/StockDetail.asp?STOCK_ID={self.stock_id}"
        soup = fetch_webpage(url, headers)
        data_rows = soup.find_all("tr", {"align": "center", "bgcolor": "white"})
        if not data_rows or len(data_rows) < 2:
            return None

        try:
            peg_cell = data_rows[1].select("td")[7]
            peg_text = peg_cell.text.strip()
            try:
                return float(peg_text)
            except ValueError:
                return None

        except (IndexError, AttributeError):
            return None

    def get_company_info(self) -> str | None:
        url = f"https://goodinfo.tw/tw/BasicInfo.asp?STOCK_ID={self.stock_id}"
        soup = fetch_webpage(url, headers)
        return soup.find_all("td", {"bgcolor": "white", "colspan": "3"}, "p")[14].text
