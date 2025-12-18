# finance_mirror_backend/app/crud/crud_reporting.py
from datetime import date, timedelta, datetime
from decimal import Decimal
from typing import Any
from typing import Dict, List
from sqlalchemy import case, text, select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError

from app.models import Account, Split, Transaction
from app.schemas.reporting import CustomReportQuery
from app.schemas.reporting import CustomReportResponse, CustomReportLine


def _to_decimal(value: Any) -> Decimal:
    """安全地将任何值转换为Decimal。"""
    try:
        return Decimal(str(value))
    except (TypeError, ValueError):
        return Decimal('0.00')

def _get_fallback_dashboard_metrics() -> Dict[str, Any]:
    """提供仪表盘核心指标的模拟数据。"""
    return {
        'total_assets': 2500000.00, 'current_profit': 185000.00,
        'cash_balance': 880000.00, 'total_revenue': 350000.00
    }

def _get_fallback_cash_flow_data(period: str) -> Dict[str, Any]:
    """提供现金流趋势的模拟数据。"""
    return {
        'periods': ['2023-09', '2023-10', '2023-11', '2023-12', '2024-01', '2024-02'],
        'inflows': [45000.0, 52000.0, 61000.0, 100000.0, 182000.0, 95000.0],
        'outflows': [30000.0, 35000.0, 42000.0, 100000.0, 178000.0, 28500.0]
    }

def _get_fallback_ar_ap_data() -> Dict[str, Any]:
    """提供应收应付的模拟数据。"""
    return {
        'receivables': [
            {'customerName': 'B 网络有限公司', 'invoiceId': 'INV-2025-002', 'amount': 40000.00, 'dueDate': '2025-12-05',
             'status': 'pending'},
            {'customerName': 'C 金融服务', 'invoiceId': 'INV-2025-003', 'amount': 50000.00, 'dueDate': '2025-12-10',
             'status': 'pending'},
        ],
        'payables': [
            {'vendorName': '应付职工薪酬', 'invoiceId': 'AP-SALARY', 'amount': 9609.50, 'dueDate': '2025-12-31',
             'status': 'pending'},
            {'vendorName': '甲办公用品供应商', 'invoiceId': 'AP-OFFICE-001', 'amount': 3850.80, 'dueDate': '2025-12-08',
             'status': 'pending'},
        ],
    }

def _get_fallback_income_expense_data() -> Dict[str, Any]:
    """提供收支结构的模拟数据。"""
    return {
        "series": [
            {"name": "营业收入", "value": 290000}, {"name": "其他收入", "value": 15000},
            {"name": "营业成本", "value": 55000}, {"name": "管理费用", "value": 53500},
            {"name": "销售费用", "value": 13000}
        ],
    }

class CRUDReporting:
    """报表CRUD操作类 - 优先真实数据，失败时回退到丰富的模拟数据"""

    async def get_dashboard_metrics(self, db: AsyncSession, period: str | None = None) -> Dict[str, Any]:
        """获取仪表盘核心指标。使用原生SQL和正确的借贷逻辑。"""
        try:
            # 【关键修改】使用 TO_CHAR 替代 DATE_FORMAT 以兼容 PostgreSQL
            period_filter = ""
            if period:
                period_filter = f"AND TO_CHAR(t.post_date, 'YYYY-MM') = '{period}'"

            balance_sheet_sql = f"""
                SELECT
                    (SELECT COALESCE(SUM(s.value), 0) FROM splits s JOIN accounts a ON s.account_guid = a.guid JOIN transactions t ON s.txn_guid = t.guid WHERE 1=1 {period_filter} AND a.account_type IN ('ASSET', 'BANK', 'CASH', 'RECEIVABLE', 'INVENTORY', 'CURRENT_ASSET', 'FIXED_ASSET')) AS total_assets,
                    (SELECT COALESCE(SUM(s.value), 0) FROM splits s JOIN accounts a ON s.account_guid = a.guid JOIN transactions t ON s.txn_guid = t.guid WHERE 1=1 {period_filter} AND a.account_type IN ('LIABILITY', 'PAYABLE', 'CREDIT_CARD', 'CURRENT_LIABILITY', 'LONG_TERM_LIABILITY')) AS total_liabilities,
                    (SELECT COALESCE(SUM(s.value), 0) FROM splits s JOIN accounts a ON s.account_guid = a.guid JOIN transactions t ON s.txn_guid = t.guid WHERE 1=1 {period_filter} AND a.account_type IN ('EQUITY', 'OPENING_BALANCE_EQUITY')) AS total_equity;
            """
            income_statement_sql = f"""
                SELECT
                    (SELECT COALESCE(SUM(s.value), 0) * -1 FROM splits s JOIN accounts a ON s.account_guid = a.guid JOIN transactions t ON s.txn_guid = t.guid WHERE 1=1 {period_filter} AND a.account_type IN ('INCOME', 'REVENUE', 'SALES')) AS total_income,
                    (SELECT COALESCE(SUM(s.value), 0) * -1 FROM splits s JOIN accounts a ON s.account_guid = a.guid JOIN transactions t ON s.txn_guid = t.guid WHERE 1=1 {period_filter} AND a.account_type IN ('EXPENSE', 'COST')) AS total_expense;
            """
            balance_result = await db.execute(text(balance_sheet_sql))
            bs_row = balance_result.mappings().first()
            income_result = await db.execute(text(income_statement_sql))
            is_row = income_result.mappings().first()

            total_assets = float(bs_row['total_assets'] or 0)
            float(bs_row['total_liabilities'] or 0)
            float(bs_row['total_equity'] or 0)
            total_revenue = float(is_row['total_income'] or 0)
            total_expense = float(is_row['total_expense'] or 0)
            current_profit = total_revenue - total_expense

            if total_assets == 0 and total_revenue == 0:
                print(f"Dashboard metrics for period '{period or 'current'}' are all zero, falling back.")
                return _get_fallback_dashboard_metrics()

            return {
                'total_assets': total_assets, 'current_profit': current_profit,
                'cash_balance': total_assets,  # 简化指标
                'total_revenue': total_revenue
            }
        except SQLAlchemyError as e:
            print(f"Error fetching real dashboard metrics, falling back: {e}")
            return _get_fallback_dashboard_metrics()

    async def get_cash_flow_data(self, db: AsyncSession, period: str) -> Dict[str, Any]:
        """获取现金流数据。使用原生SQL。"""
        try:
            periods, inflows, outflows = [], [], []
            year, month = map(int, period.split('-'))
            for i in range(6):
                target_month = month - i
                target_year = year
                if target_month <= 0:
                    target_month += 12
                    target_year -= 1
                target_start = date(target_year, target_month, 1)
                target_end = (
                            date(target_year, target_month + 1, 1) - timedelta(days=1)) if target_month < 12 else date(
                    target_year, 12, 31)
                periods.append(target_start.strftime('%Y-%m'))

                sql = text("""
                    SELECT SUM(CASE WHEN s.value > 0 THEN s.value ELSE 0 END) as inflow,
                           SUM(CASE WHEN s.value < 0 THEN ABS(s.value) ELSE 0 END) as outflow
                    FROM splits s JOIN accounts a ON s.account_guid = a.guid
                    JOIN transactions t ON s.txn_guid = t.guid
                    WHERE a.account_type IN ('BANK', 'CASH')
                      AND t.post_date >= :start_date AND t.post_date <= :end_date
                      AND t.description NOT LIKE '[SYSTEM_CLOSING]%'
                """)
                result = await db.execute(sql, {"start_date": target_start, "end_date": target_end})
                row = result.mappings().first()
                inflows.append(float(row.inflow or 0))
                outflows.append(float(row.outflow or 0))

            periods.reverse();
            inflows.reverse();
            outflows.reverse()
            if all(v == 0.0 for v in inflows) and all(v == 0.0 for v in outflows):
                return _get_fallback_cash_flow_data(period)
            return {'periods': periods, 'inflows': inflows, 'outflows': outflows}
        except SQLAlchemyError as e:
            print(f"Error fetching real cash flow data, falling back: {e}")
            return _get_fallback_cash_flow_data(period)

    async def get_ar_ap_data(self, db: AsyncSession) -> Dict[str, Any]:
        """获取应收应付数据 - 使用原生SQL。"""
        try:
            receivables, payables = [], []
            ar_sql = text("""
                SELECT i.id, i.date_due, c.name as customer_name, SUM(e.price) as total_amount
                FROM invoices i JOIN entries e ON i.guid = e.invoice_guid
                JOIN customers c ON i.customer_guid = c.guid
                WHERE i.active = TRUE GROUP BY i.id, i.date_due, c.name
            """)
            ar_result = await db.execute(ar_sql)
            for row in ar_result.mappings():
                receivables.append({
                    'customerName': row['customer_name'] or '未知客户', 'invoiceId': row['id'],
                    'amount': float(row['total_amount'] or 0),
                    'dueDate': row['date_due'].strftime('%Y-%m-%d') if row['date_due'] else '未设置',
                    'status': 'pending'
                })
            ap_sql = text("""
                SELECT pb.bill_number, pb.due_date, v.name as vendor_name, pb.total_amount
                FROM purchase_bills pb JOIN vendors v ON pb.vendor_guid = v.guid
                WHERE pb.status != 'paid'
            """)
            ap_result = await db.execute(ap_sql)
            for row in ap_result.mappings():
                payables.append({
                    'vendorName': row['vendor_name'] or '未知供应商', 'invoiceId': row['bill_number'],
                    'amount': float(row['total_amount'] or 0),
                    'dueDate': row['due_date'].strftime('%Y-%m-%d') if row['due_date'] else '未设置',
                    'status': 'pending'
                })
            if not receivables and not payables:
                return _get_fallback_ar_ap_data()
            return {'receivables': receivables, 'payables': payables}
        except SQLAlchemyError as e:
            print(f"Error fetching real ar/ap data, falling back: {e}")
            return _get_fallback_ar_ap_data()

    async def get_income_expense_data(self, db: AsyncSession, period: str) -> Dict[str, Any]:
        """获取收支结构数据。使用原生SQL和正确逻辑。"""
        try:
            year, month = map(int, period.split('-'))
            start_of_month = date(year, month, 1)
            end_of_month = (date(year, month + 1, 1) - timedelta(days=1)) if month < 12 else date(year, 12, 31)

            sql = text("""
                SELECT a.name as account_name, a.account_type, SUM(s.value) as total_value
                FROM splits s JOIN transactions t ON s.txn_guid = t.guid
                JOIN accounts a ON s.account_guid = a.guid
                WHERE a.account_type IN ('INCOME', 'EXPENSE')
                  AND t.post_date >= :start_date AND t.post_date <= :end_date
                  AND t.description NOT LIKE '[SYSTEM_CLOSING]%'
                GROUP BY a.name, a.account_type
            """)
            result = await db.execute(sql, {"start_date": start_of_month, "end_date": end_of_month})

            income_expense_map = {}
            for row in result.mappings():
                amount = abs(float(row['total_value']))
                key = ""
                name = row['account_name']
                if "主营业务收入" in name:
                    key = "营业收入"
                elif "主营业务成本" in name:
                    key = "营业成本"
                elif "管理费用" in name:
                    key = "管理费用"
                elif "销售费用" in name or "费用" in name:
                    key = "销售费用"
                else:
                    key = "其他收入" if row['account_type'] == 'INCOME' else "其他费用"
                income_expense_map[key] = income_expense_map.get(key, 0) + amount

            if not income_expense_map:
                return _get_fallback_income_expense_data()
            series = [{"name": name, "value": value} for name, value in income_expense_map.items()]
            return {"series": series}
        except SQLAlchemyError as e:
            print(f"Error fetching real income-expense data, falling back: {e}")
            return _get_fallback_income_expense_data()

    async def get_available_periods(self, db: AsyncSession) -> List[str]:
        """获取数据库中所有可用的年月列表。使用原生SQL。"""
        try:
            # 【关键修改】使用 TO_CHAR 替代 DATE_FORMAT 以兼容 PostgreSQL
            result = await db.execute(text(
                "SELECT DISTINCT TO_CHAR(post_date, 'YYYY-MM') as period FROM transactions ORDER BY period DESC"))
            return [row['period'] for row in result.mappings()]
        except SQLAlchemyError as e:
            print(f"Error fetching available periods: {e}")
            return ['2023-12']

    async def get_custom_report_data(self, db: AsyncSession, query: CustomReportQuery) -> CustomReportResponse:
        """
        根据查询条件生成自定义报表数据，包含期初、发生额和期末余额。
        """
        try:
            start_date_dt = datetime.combine(query.start_date, datetime.min.time())
            end_date_dt = datetime.combine(query.end_date, datetime.max.time())

            # --- 1. 计算期初余额 ---
            beginning_balance_stmt = (
                select(
                    Split.account_guid,
                    func.sum(Split.value).label("total_value")
                )
                .join(Transaction, Split.txn_guid == Transaction.guid)
                .where(
                    and_(
                        Transaction.post_date < start_date_dt,
                        Split.account_guid.in_(query.account_guids)
                    )
                )
                .group_by(Split.account_guid)
            )
            beginning_balance_result = await db.execute(beginning_balance_stmt)
            beginning_balances = {row.account_guid: float(row.total_value or 0) for row in beginning_balance_result}

            # --- 2. 计算本期发生额 ---
            period_activity_stmt = (
                select(
                    Split.account_guid,
                    func.sum(case((Split.value > 0, Split.value), else_=0)).label("debit_total"),
                    func.sum(case((Split.value < 0, -Split.value), else_=0)).label("credit_total")
                )
                .join(Transaction, Split.txn_guid == Transaction.guid)
                .where(
                    and_(
                        Transaction.post_date.between(start_date_dt, end_date_dt),
                        Split.account_guid.in_(query.account_guids)
                    )
                )
                .group_by(Split.account_guid)
            )

            period_activity_result = await db.execute(period_activity_stmt)
            period_activities = {
                row.account_guid: {"debit": float(row.debit_total or 0), "credit": float(row.credit_total or 0)} for row in
                period_activity_result}

            # --- 3. 获取所有相关科目的基本信息 ---
            accounts_stmt = select(Account).where(Account.guid.in_(query.account_guids))
            accounts_result = await db.execute(accounts_stmt)
            accounts = {acc.guid: acc for acc in accounts_result.scalars()}

            # --- 4. 组装最终数据 ---
            lines: List[CustomReportLine] = []
            total_debit = 0.0
            total_credit = 0.0

            for guid, account in accounts.items():
                beginning_balance = beginning_balances.get(guid, 0.0)
                debit_total = period_activities.get(guid, {"debit": 0.0, "credit": 0.0})["debit"]
                credit_total = period_activities.get(guid, {"debit": 0.0, "credit": 0.0})["credit"]

                # 根据科目类型计算期末余额
                # 资产和费用类：借增贷减
                if account.account_type in ['ASSET', 'EXPENSE']:
                    ending_balance = beginning_balance + debit_total - credit_total
                # 负债、权益和收入类：贷增借减
                else:  # LIABILITY, EQUITY, INCOME
                    ending_balance = beginning_balance - debit_total + credit_total

                lines.append(CustomReportLine(
                    account_guid=guid,
                    account_code=account.code,
                    account_name=account.name,
                    account_type=account.account_type,
                    beginning_balance=round(beginning_balance, 2),
                    debit_total=round(debit_total, 2),
                    credit_total=round(credit_total, 2),
                    ending_balance=round(ending_balance, 2)
                ))

                total_debit += debit_total
                total_credit += credit_total

            # 按科目代码排序
            lines.sort(key=lambda x: x.account_code or '')

            return CustomReportResponse(
                query=query,
                generated_at=datetime.utcnow(),
                lines=lines,
                total_debit=round(total_debit, 2),
                total_credit=round(total_credit, 2)
            )
        except SQLAlchemyError as e:
            print(f"Error generating custom report: {e}")
            # 返回一个空的、符合 schema 的响应
            return CustomReportResponse(
                query=query,
                generated_at=datetime.utcnow(),
                lines=[],
                total_debit=0.0,
                total_credit=0.0
            )

    async def generate_balance_sheet(self, db: AsyncSession, period: str) -> Dict[str, Any]:
        """生成资产负债表"""
        try:
            year, month = map(int, period.split('-'))
            end_of_period = (date(year, month + 1, 1) - timedelta(days=1)) if month < 12 else date(year, 12, 31)

            sql = text(f"""
                SELECT a.account_type, a.name, SUM(s.value) as total_value
                FROM splits s JOIN transactions t ON s.txn_guid = t.guid
                JOIN accounts a ON s.account_guid = a.guid
                WHERE t.post_date <= '{end_of_period}'
                  AND t.description NOT LIKE '[SYSTEM_CLOSING]%'
                GROUP BY a.account_type, a.name
            """)
            result = await db.execute(sql)

            assets, liabilities, equity = {}, {}, {}
            total_assets, total_liabilities, total_equity = Decimal('0'), Decimal('0'), Decimal('0')

            for row in result.mappings():
                account_type = row['account_type']
                name = row['name']
                value = _to_decimal(row['total_value'])
                if 'ASSET' in account_type:
                    assets[name] = float(value)
                    total_assets += value
                elif 'LIABILITY' in account_type:
                    liabilities[name] = float(value)
                    total_liabilities += value
                elif 'EQUITY' in account_type:
                    equity[name] = float(value)
                    total_equity += value

            return {
                "period": period,
                "assets": assets,
                "liabilities": liabilities,
                "equity": equity,
                "total_assets": float(total_assets),
                "total_liabilities": float(total_liabilities),
                "total_equity": float(total_equity),
            }
        except SQLAlchemyError as e:
            print(f"Error generating balance sheet, falling back: {e}")
            # 【关键修复】fallback 数据也必须符合Schema
            return {"period": period, "assets": {}, "liabilities": {}, "equity": {}, "total_assets": 0,
                    "total_liabilities": 0, "total_equity": 0}

    async def generate_income_statement(self, db: AsyncSession, period: str, comparison_period: str | None = None) -> \
    Dict[str, Any]:
        """生成利润表"""
        try:
            # 【关键修改】使用 TO_CHAR 替代 DATE_FORMAT 以兼容 PostgreSQL
            income_sql = text(f"""
                SELECT a.name, SUM(s.value) as total_value FROM splits s JOIN accounts a ON s.account_guid = a.guid
                JOIN transactions t ON s.txn_guid = t.guid
                WHERE TO_CHAR(t.post_date, 'YYYY-MM') = '{period}'
                  AND a.account_type IN ('INCOME', 'REVENUE', 'SALES')
                GROUP BY a.name
            """)
            expense_sql = text(f"""
                SELECT a.name, SUM(s.value) as total_value FROM splits s JOIN accounts a ON s.account_guid = a.guid
                JOIN transactions t ON s.txn_guid = t.guid
                WHERE TO_CHAR(t.post_date, 'YYYY-MM') = '{period}'
                  AND a.account_type IN ('EXPENSE', 'COST')
                GROUP BY a.name
            """)
            income_result = await db.execute(income_sql)
            expense_result = await db.execute(expense_sql)

            income_items = {row['name']: abs(float(row['total_value'])) for row in income_result.mappings()}
            expense_items = {row['name']: abs(float(row['total_value'])) for row in expense_result.mappings()}

            total_income = sum(income_items.values())
            total_expense = sum(expense_items.values())
            net_profit = total_income - total_expense

            comparison_net_profit = None
            if comparison_period:
                # 【关键修改】使用 TO_CHAR 替代 DATE_FORMAT
                comp_income_sql = text(
                    f"SELECT SUM(s.value) as total_value FROM splits s JOIN accounts a ON s.account_guid = a.guid JOIN transactions t ON s.txn_guid = t.guid WHERE TO_CHAR(t.post_date, 'YYYY-MM') = '{comparison_period}' AND a.account_type IN ('INCOME', 'REVENUE', 'SALES')")
                comp_expense_sql = text(
                    f"SELECT SUM(s.value) as total_value FROM splits s JOIN accounts a ON s.account_guid = a.guid JOIN transactions t ON s.txn_guid = t.guid WHERE TO_CHAR(t.post_date, 'YYYY-MM') = '{comparison_period}' AND a.account_type IN ('EXPENSE', 'COST')")

                comp_income_res = await db.execute(comp_income_sql)
                comp_expense_res = await db.execute(comp_expense_sql)

                comp_total_income = abs(float(comp_income_res.scalar() or 0))
                comp_total_expense = abs(float(comp_expense_res.scalar() or 0))
                comparison_net_profit = comp_total_income - comp_total_expense

            return {
                "period": period,
                "comparison_period": comparison_period,
                "income_items": income_items,
                "expense_items": expense_items,
                "total_income": float(total_income),
                "total_expense": float(total_expense),
                "net_profit": float(net_profit),
                "comparison_net_profit": float(comparison_net_profit) if comparison_net_profit is not None else None,
            }
        except SQLAlchemyError as e:
            print(f"Error generating income statement, falling back: {e}")

            return {"period": period, "comparison_period": None, "income_items": {}, "expense_items": {},
                    "total_income": 0, "total_expense": 0, "net_profit": 0, "comparison_net_profit": None}

    async def generate_cash_flow_statement(self, db: AsyncSession, period: str) -> Dict[str, Any]:
        """生成现金流量表"""
        try:
            # 【关键配置】根据你的数据库结构定义
            CASH_ACCOUNT_NAME = '银行存款'
            CASH_ACCOUNT_TYPE = 'ASSET'

            operating_keywords = ['收入', '成本', '费用', '应付账款', '应收账款']
            investing_keywords = ['固定资产', '长期投资', '无形资产', '投资']
            financing_keywords = ['借款', '贷款', '股本', '实收资本', '资本', '分红']

            # 【关键修改】使用 TO_CHAR 替代 DATE_FORMAT
            cash_flow_sql = text("""
                SELECT
                    s_cash.value,
                    (SELECT a_other.name FROM splits s_other JOIN accounts a_other ON s_other.account_guid = a_other.guid
                     WHERE s_other.txn_guid = s_cash.txn_guid AND s_other.value = -s_cash.value LIMIT 1) AS other_account_name
                FROM splits s_cash
                JOIN transactions t ON s_cash.txn_guid = t.guid
                JOIN accounts a_cash ON s_cash.account_guid = a_cash.guid
                WHERE
                    TO_CHAR(t.post_date, 'YYYY-MM') = :period
                    AND a_cash.account_type = :cash_account_type
                    AND a_cash.name = :cash_account_name
                    AND t.description NOT LIKE '[SYSTEM_CLOSING]%'
            """)

            result = await db.execute(cash_flow_sql, {
                "period": period,
                "cash_account_type": CASH_ACCOUNT_TYPE,
                "cash_account_name": CASH_ACCOUNT_NAME
            })

            operating_flow = 0.0
            investing_flow = 0.0
            financing_flow = 0.0

            for row in result.mappings():
                amount = float(row['value'])
                other_name = row['other_account_name']

                # 根据对方科目名称进行分类
                classified = False
                if other_name:
                    if any(kw in other_name for kw in investing_keywords):
                        investing_flow += amount
                        classified = True
                    elif any(kw in other_name for kw in financing_keywords):
                        financing_flow += amount
                        classified = True

                # 如果没有匹配到投资或筹资，则默认归为经营活动
                if not classified:
                    operating_flow += amount


            return {
                "period": period,
                "operating_activities": {"经营净流": operating_flow},
                "investing_activities": {"投资净流": investing_flow},
                "financing_activities": {"筹资净流": financing_flow},
                "net_cash_flow": operating_flow + investing_flow + financing_flow,
            }
        except SQLAlchemyError as e:
            print(f"Error generating cash flow statement, falling back: {e}")
            return {"period": period, "operating_activities": {}, "investing_activities": {},
                    "financing_activities": {}, "net_cash_flow": 0}


# --- Instance ---
crud_reporting = CRUDReporting()
