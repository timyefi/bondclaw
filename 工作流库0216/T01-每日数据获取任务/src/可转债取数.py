"""获取需要采集的可转债代码"""
        try:
            query = """
                select distinct trade_code
                from bond.marketinfo_equity 
                where ths_bond_balance_bond>0
                and dt>=DATE_SUB(CURDATE(), INTERVAL 1 YEAR)
            """



# 分别获取每个指标
            indicators_config = [
                {'name': 'ths_bond_close_cbond', 'param': '103'},  # 收盘价需要参数103
                {'name': 'ths_new_bond_amt_cbond', 'param': ''},  # 成交额
                {'name': 'ths_pure_bond_premium_rate_cbond', 'param': ''},  # 纯债溢价率
                {'name': 'ths_pure_bond_ytm_cbond', 'param': ''},  # 纯债到期收益率
                {'name': 'ths_conversion_premium_rate_cbond', 'param': ''},  # 转股溢价率
                {'name': 'ths_conver_pe_cbond', 'param': ''},  # 转股市盈率
                {'name': 'ths_stock_pe_cbond', 'param': ''},  # 正股市盈率
                {'name': 'ths_stock_pb_cbond', 'param': ''},  # 正股市净率
                {'name': 'ths_conver_pb_cbond', 'param': ''}  # 转股市净率
            ]
            
            all_data = []
            
            # 逐个获取指标数据
            for indicator in indicators_config:
                result = THS_DS(
                    bond_code,
                    indicator['name'],
                    indicator['param'],
                    '',
                    start_date,
                    end_date
                )
                
                if result.data is None:
                    self.logger.error(f"获取{indicator['name']}数据失败: {bond_code}, {result.errmsg}")
                    continue
                    
                df = result.data
                if not df.empty:
                    all_data.append(df)


# 重命名列
            rename_dict = {
                'time': 'dt',
                'thscode': 'trade_code',
                'ths_bond_close_cbond': 'close',
                'ths_new_bond_amt_cbond': 'amount',
                'ths_pure_bond_premium_rate_cbond': 'pure_premium',
                'ths_pure_bond_ytm_cbond': 'ytm',
                'ths_conversion_premium_rate_cbond': 'conv_premium',
                'ths_conver_pe_cbond': 'conv_pe',
                'ths_stock_pe_cbond': 'stock_pe',
                'ths_stock_pb_cbond': 'stock_pb',
                'ths_conver_pb_cbond': 'conv_pb'
            }
            final_df = final_df.rename(columns=rename_dict)
		
		
		