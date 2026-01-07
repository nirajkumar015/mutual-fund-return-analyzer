import streamlit as st
import pandas as pd

# ---------------- PAGE CONFIG ----------------
st.set_page_config(
    page_title="Mutual Fund Return Analyzer",
    page_icon="📈",
    layout="centered"
)

st.title("📈 Mutual Fund Return Analyzer")
st.write(
    "Complete investment & retirement planning tool with SIP, Lumpsum, "
    "inflation, tax adjustment, goal planning, and retirement planning."
)

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
    step=500
)

years = st.number_input(
    "Investment Duration (Years)",
    min_value=1,
    step=1
)

goal_amount = st.number_input(
    "🎯 Financial Goal Amount (₹)",
    min_value=0,
    step=100000
)

if st.button("Calculate SIP Returns"):
    months = years * 12
    monthly_rate = expected_return / 100 / 12

    total_invested = monthly_investment * months

    future_value = monthly_investment * (
        ((1 + monthly_rate) ** months - 1) / monthly_rate
    ) * (1 + monthly_rate)

    profit = future_value - total_invested

    tax_amount = profit * (tax_rate / 100)
    post_tax_value = future_value - tax_amount

    post_tax_cagr = ((post_tax_value / total_invested) ** (1 / years) - 1) * 100
    real_cagr = ((1 + post_tax_cagr / 100) / (1 + inflation_rate / 100) - 1) * 100

    st.success(f"💵 Total Invested: ₹{total_invested:,.0f}")
    st.success(f"📈 Final Value (After Tax): ₹{post_tax_value:,.0f}")
    st.success(f"🟢 Profit (After Tax): ₹{post_tax_value - total_invested:,.0f}")
    st.info(f"📊 CAGR (After Tax): {post_tax_cagr:.2f}%")
    st.warning(f"📉 Inflation-Adjusted CAGR: {real_cagr:.2f}%")

    if goal_amount > 0:
        st.divider()
        st.subheader("🎯 Goal-Based Planning")

        if post_tax_value >= goal_amount:
            st.success("✅ Goal achievable with current SIP.")
        else:
            st.error("❌ Goal NOT achievable with current SIP.")

            required_sip = (
                goal_amount * monthly_rate /
                (((1 + monthly_rate) ** months - 1) * (1 + monthly_rate))
            )

            st.info(f"📌 Required Monthly SIP: ₹{required_sip:,.0f}")

# ================= RETIREMENT PLANNER =================
st.divider()
st.subheader("🧓 Retirement Planner")

current_age = st.number_input("Current Age", min_value=18, max_value=60, value=30)
retirement_age = st.number_input("Retirement Age", min_value=40, max_value=75, value=60)
life_expectancy = st.number_input("Life Expectancy", min_value=70, max_value=100, value=85)

monthly_expense_today = st.number_input(
    "Monthly Expense (Today's Value ₹)",
    min_value=5000,
    step=5000,
    value=30000
)

if st.button("Calculate Retirement Plan"):
    years_to_retirement = retirement_age - current_age
    retirement_years = life_expectancy - retirement_age

    # Expense at retirement (inflation adjusted)
    monthly_expense_retirement = monthly_expense_today * (
        (1 + inflation_rate / 100) ** years_to_retirement
    )

    annual_expense_retirement = monthly_expense_retirement * 12

    # Retirement corpus required (simple annuity approximation)
    real_return = (1 + expected_return / 100) / (1 + inflation_rate / 100) - 1
    retirement_corpus = annual_expense_retirement * (
        (1 - (1 + real_return) ** (-retirement_years)) / real_return
    )

    st.success(f"💸 Monthly Expense at Retirement: ₹{monthly_expense_retirement:,.0f}")
    st.success(f"🏦 Retirement Corpus Required: ₹{retirement_corpus:,.0f}")

    # SIP required for retirement
    months = years_to_retirement * 12
    monthly_rate = expected_return / 100 / 12

    required_sip = (
        retirement_corpus * monthly_rate /
        (((1 + monthly_rate) ** months - 1) * (1 + monthly_rate))
    )

    st.info(f"📌 SIP Required for Retirement: ₹{required_sip:,.0f}")

    if monthly_investment >= required_sip:
        st.success("✅ Your current SIP is sufficient for retirement.")
    else:
        st.warning(
            f"⚠ Increase SIP by ₹{required_sip - monthly_investment:,.0f} "
            "to meet retirement goal."
        )






    





