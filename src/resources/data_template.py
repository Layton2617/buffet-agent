class DataTemplate:
    """
    数据传递模板类：用于根据外部API接口需求，生成标准化数据结构。
    用户可实例化本类，传入实际数据，统一管理和导出API所需格式。
    """

    def __init__(self, template_type: str, **kwargs):
        """
        初始化数据模板对象。
        :param template_type: 模板类型，如 'dcf', 'pe', 'buffett_score', 'margin', 'portfolio', 'beliefs_update', 'corpus_search'
        :param kwargs: 实际数据字段
        """
        self.template_type = template_type
        self.data = self._init_template(template_type)
        # 用用户传入的数据覆盖默认空值
        for k, v in kwargs.items():
            if k in self.data:
                self.data[k] = v

    def _init_template(self, template_type):
        """
        根据模板类型初始化字段结构。
        """
        if template_type == 'dcf':
            return {
                "free_cash_flows": [],           # 自由现金流列表，float
                "terminal_growth_rate": None,    # 终值增长率，float
                "discount_rate": None            # 贴现率，float
            }
        elif template_type == 'pe':
            return {
                "current_pe": None,              # 当前市盈率，float
                "industry_avg_pe": None,         # 行业平均市盈率，float
                "historical_pe_range": [],       # 历史市盈率区间，list[float]
                "earnings_growth_rate": None     # 盈利增长率，float
            }
        elif template_type == 'buffett_score':
            return {
                "roe": None,                     # 净资产收益率，float
                "debt_to_equity": None,         # 负债率，float
                "profit_margin": None,          # 利润率，float
                "revenue_growth": None,         # 收入增长率，float
                "pe_ratio": None                # 市盈率，float
            }
        elif template_type == 'margin':
            return {
                "intrinsic_value": None,         # 内在价值，float
                "current_price": None,           # 当前价格，float
                "minimum_margin": 0.20           # 最低安全边际，float（可选，默认0.2）
            }
        elif template_type == 'portfolio':
            return {
                "symbols": []                    # 股票代码列表，list[str]
            }
        elif template_type == 'beliefs_update':
            return {
                "news_summary": None             # 新闻摘要，str
            }
        elif template_type == 'corpus_search':
            return {
                "query": None,                   # 检索内容，str
                "top_k": 3                       # 返回条数，int
            }
        else:
            raise ValueError(f"未知模板类型: {template_type}")

    def update(self, **kwargs):
        """
        更新/补充数据字段。
        """
        for k, v in kwargs.items():
            if k in self.data:
                self.data[k] = v
            else:
                raise ValueError(f"未知字段: {k}")

    def to_api_dict(self):
        """
        导出标准API格式的字典。
        """
        return self.data.copy()

    def validate(self):
        """
        简单校验必填字段（None或空列表/字符串）。
        返回缺失字段列表。
        """
        missing = []
        for k, v in self.data.items():
            if v is None or (isinstance(v, (list, str)) and not v):
                missing.append(k)
        return missing 