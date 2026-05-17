"""Chart and analytics helper functions"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from datetime import datetime, timedelta
import streamlit as st


def render_pie_chart(by_category: dict, total_spent: float):
    """Pie/donut chart with small slices consolidated into Others."""
    if not by_category:
        return
    threshold = total_spent * 0.03
    main, others_val = {}, 0
    for cat, val in by_category.items():
        if val < threshold:
            others_val += val
        else:
            main[cat] = val
    if others_val > 0:
        main["Others"] = others_val

    cats = list(main.keys())
    vals = list(main.values())
    palette = ["#1B2A4A", "#2d4373", "#4a6fa5", "#FF6B35", "#6b8cae",
               "#e8913a", "#3d5a80", "#98c1d9", "#a0522d", "#27ae60",
               "#8e44ad", "#2c3e50", "#d4a437", "#c0392b"]

    fig, ax = plt.subplots(figsize=(4.5, 4.5))
    fig.patch.set_alpha(0)
    wedges, _, autotexts = ax.pie(
        vals, autopct=lambda p: f"{p:.0f}%" if p > 5 else "",
        colors=palette[:len(cats)], startangle=90, pctdistance=0.78,
        wedgeprops=dict(width=0.42, edgecolor="white", linewidth=2),
    )
    for t in autotexts:
        t.set_fontsize(8)
        t.set_color("#ffffff")
        t.set_fontweight("bold")
    centre = plt.Circle((0, 0), 0.58, fc="white")
    ax.add_artist(centre)
    ax.text(0, 0.05, f"P {total_spent:,.0f}", ha="center", va="center",
            fontsize=15, fontweight="bold", color="#1B2A4A", family="sans-serif")
    ax.text(0, -0.1, "total spent", ha="center", va="center",
            fontsize=8, color="#8a96a6", family="sans-serif")

    # Legend below
    legend = ax.legend(wedges, [f"{c}  P {v:,.0f}" for c, v in zip(cats, vals)],
                       loc="upper center", bbox_to_anchor=(0.5, -0.02),
                       ncol=2, fontsize=8, frameon=False)
    for t in legend.get_texts():
        t.set_color("#1B2A4A")

    st.pyplot(fig, use_container_width=False)
    plt.close(fig)


def render_monthly_bar(all_expenses: list, budget: float):
    """Bar chart of monthly totals for the last 6 months with budget line."""
    if not all_expenses:
        st.info("Not enough data for monthly trends yet.")
        return
    df = pd.DataFrame(all_expenses)
    df["bill_date"] = pd.to_datetime(df["bill_date"])
    df["month"] = df["bill_date"].dt.to_period("M")

    monthly = df.groupby("month")["amount"].sum().sort_index()
    last6 = monthly.tail(6)
    if last6.empty:
        return

    labels = [str(p) for p in last6.index]
    values = last6.values
    colors = ["#27ae60" if v <= budget else ("#FF6B35" if v <= budget * 1.2 else "#e74c3c")
              for v in values]

    fig, ax = plt.subplots(figsize=(7, 3.5))
    fig.patch.set_alpha(0)
    ax.bar(labels, values, color=colors, width=0.55, edgecolor="white", linewidth=1, zorder=3)
    ax.axhline(y=budget, color="#1B2A4A", linestyle="--", linewidth=1.2, label=f"Budget: P {budget:,.0f}", zorder=2)
    ax.set_facecolor("#fafbfc")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color("#e0e0e0")
    ax.spines["bottom"].set_color("#e0e0e0")
    ax.tick_params(colors="#6b7c93", labelsize=9)
    ax.set_ylabel("Amount (PHP)", fontsize=9, color="#6b7c93")
    ax.legend(fontsize=8, loc="upper right", frameon=False)
    for i, v in enumerate(values):
        ax.text(i, v + budget * 0.02, f"P {v:,.0f}", ha="center", fontsize=8,
                fontweight="bold", color="#1B2A4A")
    fig.tight_layout()
    st.pyplot(fig, use_container_width=True)
    plt.close(fig)


def render_payment_chart(by_payment: dict):
    """Horizontal bar chart of spend per payment method."""
    if not by_payment:
        return
    methods = list(by_payment.keys())
    amounts = list(by_payment.values())
    palette = ["#1B2A4A", "#FF6B35", "#4a6fa5", "#27ae60", "#e8913a", "#8e44ad", "#3d5a80"]

    fig, ax = plt.subplots(figsize=(5, max(2.5, len(methods) * 0.6)))
    fig.patch.set_alpha(0)
    bars = ax.barh(methods, amounts, color=palette[:len(methods)], height=0.5, edgecolor="white")
    ax.set_facecolor("#fafbfc")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color("#e0e0e0")
    ax.spines["bottom"].set_color("#e0e0e0")
    ax.tick_params(colors="#6b7c93", labelsize=9)
    for bar, val in zip(bars, amounts):
        ax.text(bar.get_width() + max(amounts) * 0.02, bar.get_y() + bar.get_height() / 2,
                f"P {val:,.0f}", va="center", fontsize=8, fontweight="bold", color="#1B2A4A")
    fig.tight_layout()
    st.pyplot(fig, use_container_width=True)
    plt.close(fig)


def render_price_tracker(all_expenses: list):
    """Line chart tracking price of a selected item/brand over time."""
    if not all_expenses:
        st.info("Not enough data for price tracking yet.")
        return
    df = pd.DataFrame(all_expenses)
    df["bill_date"] = pd.to_datetime(df["bill_date"])
    df["label"] = df.apply(
        lambda r: f"{r.get('brand', '')} {r.get('description', '')}".strip(), axis=1
    )
    # Items that appear at least twice
    counts = df["label"].value_counts()
    recurring = counts[counts >= 2].index.tolist()
    if not recurring:
        st.info("Need at least 2 purchases of the same item to show price trends.")
        return

    selected = st.selectbox("Select item to track", recurring)
    subset = df[df["label"] == selected].sort_values("bill_date")

    fig, ax = plt.subplots(figsize=(6, 3))
    fig.patch.set_alpha(0)
    dates = subset["bill_date"].dt.strftime("%b %d")
    prices = subset["amount"].values
    ax.plot(dates, prices, marker="o", color="#1B2A4A", linewidth=2, markersize=6, zorder=3)
    ax.fill_between(range(len(prices)), prices, alpha=0.08, color="#1B2A4A")
    ax.set_facecolor("#fafbfc")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color("#e0e0e0")
    ax.spines["bottom"].set_color("#e0e0e0")
    ax.tick_params(colors="#6b7c93", labelsize=8)
    ax.set_ylabel("Price (PHP)", fontsize=9, color="#6b7c93")
    for i, p in enumerate(prices):
        ax.annotate(f"P {p:,.0f}", (i, p), textcoords="offset points",
                    xytext=(0, 10), ha="center", fontsize=7, color="#1B2A4A", fontweight="bold")
    fig.tight_layout()
    st.pyplot(fig, use_container_width=True)
    plt.close(fig)


def render_payment_category_heatmap(expenses: list):
    """Cross-reference table: payment method vs category."""
    if not expenses:
        return
    df = pd.DataFrame(expenses)
    pivot = pd.pivot_table(df, values="amount", index="payment_method",
                           columns="category", aggfunc="sum", fill_value=0)
    # Format as peso amounts
    formatted = pivot.map(lambda x: f"P {x:,.0f}" if x > 0 else "-")
    st.dataframe(formatted, use_container_width=True)
