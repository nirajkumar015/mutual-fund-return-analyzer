import streamlit as st
import pandas as pd
from datetime import date
from dateutil.relativedelta import relativedelta


# ---------------- PAGE CONFIG ----------------
st.set_page_config(
    page_title="Mutual Fund Return Analyzer",
    page_icon="📈",
    layout="centered"
)

st.title("📈 Mutual Fund Return Analyzer")
st.write(
    "Complete investment & retirement planning tool with SIP, "
    "inflation, tax adjustment, goal planning, retirement planning, "
    "and mutual fund comparison."
)


# ================= HELPER FUNCTIONS =================

def calculate_sip_future_value(monthly_investment, annual_return, years):
    """
    SIP invested at the beginning of every month.
    Annual return is converted to an equivalent monthly rate.
    """

    months = int(years * 12)

    # Convert effective annual return to equivalent monthly return
    monthly_rate = (1 + annual_return / 100) ** (1 / 12) - 1

    if monthly_rate == 0:
        return monthly_investment * months

    future_value = monthly_investment * (
        ((1 + monthly_rate) ** months - 1) / monthly_rate
    ) * (1 + monthly_rate)

    return future_value


def calculate_sip_tax(future_value, total_invested, tax_rate):
    """
    Simplified capital-gains tax:
    Tax is applied only to the total investment profit.

    NOTE:
    This is an educational simplification and does not model
    actual Indian capital-gains exemptions/holding-period rules.
    """

    profit = max(future_value - total_invested, 0)

    tax_amount = profit * (tax_rate / 100)

    post_tax_value = future_value - tax_amount

    return profit, tax_amount, post_tax_value


def calculate_xirr(cashflows, dates):
    """
    Calculates annualized return for irregular cash flows.

    For a monthly SIP, each investment happens at a different date,
    so XIRR is more appropriate than:

    (Final Value / Total Invested)^(1/years) - 1
    """

    if len(cashflows) != len(dates):
        return None

    if sum(cf > 0 for cf in cashflows) == 0:
        return None

    if sum(cf < 0 for cf in cashflows) == 0:
        return None

    base_date = dates[0]

    def npv(rate):
        return sum(
            cf / ((1 + rate) ** ((d - base_date).days / 365.0))
            for cf, d in zip(cashflows, dates)
        )

    # Binary search over a wide but reasonable range
    low = -0.9999
    high = 10.0

    try:
        npv_low = npv(low)
        npv_high = npv(high)

        # If no sign change, XIRR cannot be reliably found
        if npv_low * npv_high > 0:
            return None

        for _ in range(200):
            mid = (low + high) / 2
            npv_mid = npv(mid)

            if abs(npv_mid) < 1e-7:
                return mid

            if npv_low * npv_mid <= 0:
                high = mid
                npv_high = npv_mid
            else:
                low = mid
                npv_low = npv_mid

        return (low + high) / 2

    except Exception:
        return None


def calculate_sip_xirr(monthly_investment, post_tax_value, years):
    """
    XIRR for a SIP where investments are made at the beginning
    of every month and the final value is received at the end.
    """

    months = int(years * 12)

    start_date = date.today()

    cashflows = []
    dates = []

    # SIP investments
    for i in range(months):
        investment_date = start_date + relativedelta(months=i)

        cashflows.append(-monthly_investment)
        dates.append(investment_date)

    # Final value received after the investment period
    final_date = start_date + relativedelta(months=months)

    cashflows.append(post_tax_value)
    dates.append(final_date)

    xirr = calculate_xirr(cashflows, dates)

    if xirr is None:
        return None

    return xirr * 100


def calculate_real_return(nominal_return, inflation):
    """
    Fisher equation for inflation-adjusted / real return.
    """

    return (
        ((1 + nominal_return / 100) /
         (1 + inflation / 100)) - 1
    ) * 100


def calculate_required_sip_for_goal(
    goal_amount,
    annual_return,
    years,
    tax_rate
):
    """
    Finds the monthly SIP required to reach a target AFTER the
    simplified capital-gains tax.

    Uses binary search because tax is applied to profit.
    """

    months = int(years * 12)

    monthly_rate = (
        (1 + annual_return / 100) ** (1 / 12)
    ) - 1

    if monthly_rate == 0:
        # No investment growth
        return goal_amount / months

    def after_tax_value(monthly_sip):

        future_value = monthly_sip * (
            ((1 + monthly_rate) ** months - 1) /
            monthly_rate
        ) * (1 + monthly_rate)

        total_invested = monthly_sip * months

        profit = max(future_value - total_invested, 0)

        tax = profit * (tax_rate / 100)

        return future_value - tax

    low = 0
    high = goal_amount / months * 10

    # Increase upper limit if necessary
    while after_tax_value(high) < goal_amount:
        high *= 2

        if high > 1e9:
            return None

    for _ in range(200):

        mid = (low + high) / 2

        if after_tax_value(mid) >= goal_amount:
            high = mid
        else:
            low = mid

    return high


def calculate_retirement_corpus(
    monthly_expense_today,
    years_to_retirement,
    retirement_years,
    inflation_rate,
    expected_return
):
    """
    Calculates retirement corpus at retirement.

    Step 1:
    Inflate today's monthly expense to retirement.

    Step 2:
    Calculate the present value at retirement of the future
    retirement expenses using the nominal portfolio return.

    This keeps the calculation internally consistent:
    nominal expenses + nominal return.
    """

    monthly_expense_retirement = (
        monthly_expense_today *
        (1 + inflation_rate / 100) ** years_to_retirement
    )

    annual_expense_retirement = monthly_expense_retirement * 12

    annual_return = expected_return / 100

    if annual_return == 0:
        retirement_corpus = (
            annual_expense_retirement * retirement_years
        )
    else:
        retirement_corpus = annual_expense_retirement * (
            (1 - (1 + annual_return) ** (-retirement_years))
            / annual_return
        )

    return monthly_expense_retirement, retirement_corpus


def calculate_required_retirement_sip(
    retirement_corpus,
    annual_return,
    years_to_retirement,
    tax_rate
):
    """
    Calculates the monthly SIP required to accumulate the retirement
    corpus after the simplified capital-gains tax.
    """

    return calculate_required_sip_for_goal(
        retirement_corpus,
        annual_return,
        years_to_retirement,
        tax_rate
    )


# ================= MUTUAL FUND DATA =================

fund_data = {
    "Fund Name": [
        "Large Cap Fund",
        "Index Fund",
        "Mid Cap Fund",
        "Small Cap Fund",
        "Flexi Cap Fund"
    ],
    "Expected Return (%)": [10, 9, 13, 15, 12],
    "Volatility (%)": [8, 7, 14, 20, 12]
}

fund_df = pd.DataFrame(fund_data)


# ================= ECONOMIC ASSUMPTIONS =================

st.divider()
st.subheader("⚙️ Economic Assumptions")

inflation_rate = st.number_input(
    "Expected Inflation Rate (%)",
    min_value=0.0,
    step=0.5,
    value=6.0
)

tax_rate = st.number_input(
    "Capital Gains Tax Rate (%)",
    min_value=0.0,
    step=1.0,
    value=10.0
)

expected_return = st.number_input(
    "Expected Portfolio Return (%)",
    min_value=1.0,
    step=0.5,
    value=12.0
)


# ================= SIP CALCULATOR =================

st.divider()
st.subheader("💰 SIP Calculator")

monthly_investment = st.number_input(
    "Monthly SIP Amount (₹)",
    min_value=500,
    step=500,
    value=5000
)

years = st.number_input(
    "Investment Duration (Years)",
    min_value=1,
    step=1,
    value=10
)

goal_amount = st.number_input(
    "🎯 Financial Goal Amount (₹)",
    min_value=0,
    step=100000
)


if st.button("Calculate SIP Returns"):

    months = int(years * 12)

    # Total amount invested
    total_invested = monthly_investment * months

    # SIP future value
    future_value = calculate_sip_future_value(
        monthly_investment,
        expected_return,
        years
    )

    # Tax calculation
    profit_before_tax, tax_amount, post_tax_value = (
        calculate_sip_tax(
            future_value,
            total_invested,
            tax_rate
        )
    )

    # XIRR after tax
    post_tax_cagr = calculate_sip_xirr(
        monthly_investment,
        post_tax_value,
        years
    )

    # Inflation-adjusted return
    if post_tax_cagr is not None:
        real_cagr = calculate_real_return(
            post_tax_cagr,
            inflation_rate
        )
    else:
        real_cagr = None

    st.success(
        f"💵 Total Invested: ₹{total_invested:,.0f}"
    )

    st.success(
        f"📈 Final Value (After Tax): ₹{post_tax_value:,.0f}"
    )

    st.success(
        f"🟢 Profit (After Tax): "
        f"₹{post_tax_value - total_invested:,.0f}"
    )

    if post_tax_cagr is not None:
        st.info(
            f"📊 CAGR / XIRR (After Tax): "
            f"{post_tax_cagr:.2f}%"
        )
    else:
        st.info(
            "📊 CAGR / XIRR: Unable to calculate"
        )

    if real_cagr is not None:
        st.warning(
            f"📉 Inflation-Adjusted CAGR: "
            f"{real_cagr:.2f}%"
        )

    # Show tax information
    st.caption(
        f"Capital Gains Tax (simplified): "
        f"₹{tax_amount:,.0f}"
    )

    st.caption(
        "Tax calculation is a simplified educational assumption "
        "and does not model actual Indian capital-gains exemptions "
        "or holding-period rules."
    )


    # ================= GOAL PLANNING =================

    if goal_amount > 0:

        st.divider()
        st.subheader("🎯 Goal-Based Planning")

        if post_tax_value >= goal_amount:

            st.success(
                "✅ Goal achievable with current SIP."
            )

        else:

            st.error(
                "❌ Goal NOT achievable with current SIP."
            )

            required_sip = calculate_required_sip_for_goal(
                goal_amount,
                expected_return,
                years,
                tax_rate
            )

            if required_sip is not None:

                st.info(
                    f"📌 Required Monthly SIP: "
                    f"₹{required_sip:,.0f}"
                )


# ================= RETIREMENT PLANNER =================

st.divider()
st.subheader("🧓 Retirement Planner")

current_age = st.number_input(
    "Current Age",
    min_value=18,
    max_value=60,
    value=30
)

retirement_age = st.number_input(
    "Retirement Age",
    min_value=40,
    max_value=75,
    value=60
)

life_expectancy = st.number_input(
    "Life Expectancy",
    min_value=70,
    max_value=100,
    value=85
)

monthly_expense_today = st.number_input(
    "Monthly Expense (Today's Value ₹)",
    min_value=5000,
    step=5000,
    value=30000
)


if st.button("Calculate Retirement Plan"):

    # Validate ages
    if retirement_age <= current_age:

        st.error(
            "❌ Retirement age must be greater than current age."
        )

    elif life_expectancy <= retirement_age:

        st.error(
            "❌ Life expectancy must be greater than retirement age."
        )

    else:

        years_to_retirement = (
            retirement_age - current_age
        )

        retirement_years = (
            life_expectancy - retirement_age
        )

        # Retirement expense + corpus
        (
            monthly_expense_retirement,
            retirement_corpus
        ) = calculate_retirement_corpus(
            monthly_expense_today,
            years_to_retirement,
            retirement_years,
            inflation_rate,
            expected_return
        )

        # Real return shown for information
        real_return = calculate_real_return(
            expected_return,
            inflation_rate
        )

        st.success(
            f"💸 Monthly Expense at Retirement: "
            f"₹{monthly_expense_retirement:,.0f}"
        )

        st.success(
            f"🏦 Retirement Corpus Required: "
            f"₹{retirement_corpus:,.0f}"
        )

        st.info(
            f"📉 Expected Real Return After Inflation: "
            f"{real_return:.2f}%"
        )

        # Required SIP for retirement corpus
        required_sip = calculate_required_retirement_sip(
            retirement_corpus,
            expected_return,
            years_to_retirement,
            tax_rate
        )

        if required_sip is not None:

            st.info(
                f"📌 SIP Required for Retirement: "
                f"₹{required_sip:,.0f}"
            )

            if monthly_investment >= required_sip:

                st.success(
                    "✅ Your current SIP is sufficient "
                    "for retirement."
                )

            else:

                increase = (
                    required_sip - monthly_investment
                )

                st.warning(
                    f"⚠ Increase SIP by ₹{increase:,.0f} "
                    "to meet retirement goal."
                )


# ================= MUTUAL FUND COMPARISON =================

st.divider()
st.subheader("📊 Mutual Fund Comparison (Risk vs Return)")

tab1, tab2 = st.tabs(
    ["📈 Compare Funds", "ℹ️ Risk Info"]
)


with tab1:

    selected_funds = st.multiselect(
        "Select Mutual Funds",
        fund_df["Fund Name"]
    )

    sip_amount = st.number_input(
        "Monthly SIP for Comparison (₹)",
        min_value=500,
        step=500,
        value=5000
    )

    invest_years = st.number_input(
        "Investment Duration (Years)",
        min_value=1,
        step=1,
        value=5
    )

    if st.button("Compare Funds"):

        if len(selected_funds) < 2:

            st.warning(
                "Please select at least two funds."
            )

        else:

            months = int(invest_years * 12)

            results = []

            for fund in selected_funds:

                row = fund_df[
                    fund_df["Fund Name"] == fund
                ].iloc[0]

                annual_return = row[
                    "Expected Return (%)"
                ]

                volatility = row[
                    "Volatility (%)"
                ]

                future_value = calculate_sip_future_value(
                    sip_amount,
                    annual_return,
                    invest_years
                )

                if volatility <= 8:

                    risk = "Low Risk"

                elif volatility <= 14:

                    risk = "Medium Risk"

                else:

                    risk = "High Risk"

                results.append([
                    fund,
                    annual_return,
                    volatility,
                    risk,
                    future_value
                ])

            result_df = pd.DataFrame(
                results,
                columns=[
                    "Fund Name",
                    "Expected Return (%)",
                    "Volatility (%)",
                    "Risk Level",
                    "Final SIP Value (₹)"
                ]
            )

            st.dataframe(
                result_df,
                use_container_width=True
            )

            best_fund = result_df.loc[
                result_df[
                    "Final SIP Value (₹)"
                ].idxmax()
            ]

            st.success(
                f"🏆 Best Fund Based on Returns: "
                f"{best_fund['Fund Name']} "
                f"(₹{best_fund['Final SIP Value (₹)']:,.0f})"
            )


with tab2:

    st.info(
        "🔹 Low Risk: Stable returns with low volatility\n\n"
        "🔹 Medium Risk: Balanced growth and volatility\n\n"
        "🔹 High Risk: Higher potential returns with higher fluctuations\n\n"
        "Risk is approximated using volatility."
    )


# ================= DISCLAIMER =================

st.caption(
    "Disclaimer: This tool is for educational purposes only "
    "and does not provide financial advice. SIP returns are "
    "illustrative and actual mutual fund returns may vary."
)


    





