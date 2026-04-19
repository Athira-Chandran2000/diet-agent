import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
from langchain_core.messages import HumanMessage, AIMessage

from database import get_session, UserProfile, MealLog, WeightLog, init_db
from agents.orchestrator import run_agent
from tools.profile_tools import compute_targets

st.set_page_config(page_title="AI Diet Coach", page_icon="🥗", layout="wide")
init_db()

# ---------- CUSTOM CSS ----------
st.markdown("""
<style>
.main-header {font-size:2.4rem; font-weight:700; background:linear-gradient(90deg,#11998e,#38ef7d);
    -webkit-background-clip:text; -webkit-text-fill-color:transparent;}
.metric-card {background:#1e1e2e; padding:1rem; border-radius:12px; border-left:4px solid #38ef7d;}
.stChatMessage {border-radius:12px;}
</style>""", unsafe_allow_html=True)

# ---------- SIDEBAR: PROFILE & LOGIN ----------
with st.sidebar:
    st.markdown("## 🔑 Login")
    if "username" not in st.session_state:
        st.session_state.username = None
        
    if not st.session_state.username:
        user_input = st.text_input("Enter Username to start:")
        if st.button("Login"):
            if user_input:
                st.session_state.username = user_input
                st.rerun()
        st.stop()
        
    st.success(f"Logged in as {st.session_state.username}")
    if st.button("Logout"):
        st.session_state.username = None
        st.rerun()

    st.markdown("---")
    st.markdown("## 👤 Profile Details")
    session = get_session()
    profile = session.query(UserProfile).filter_by(name=st.session_state.username).first()

    with st.expander("✏️ Edit Profile", expanded=(profile is None)):
        name = st.text_input("Username", value=st.session_state.username, disabled=True)
        col1, col2 = st.columns(2)
        age = col1.number_input("Age", 10, 100, profile.age if profile else 25)
        gender = col2.selectbox("Gender", ["male", "female"],
                                 index=0 if not profile or profile.gender == "male" else 1)
        height = col1.number_input("Height (cm)", 100.0, 250.0,
                                    profile.height_cm if profile else 170.0)
        weight = col2.number_input("Weight (kg)", 30.0, 300.0,
                                    profile.weight_kg if profile else 70.0)
        activity = st.selectbox("Activity Level",
            ["sedentary", "light", "moderate", "active", "very_active"],
            index=["sedentary","light","moderate","active","very_active"].index(
                profile.activity_level) if profile else 2)
        goal = st.selectbox("Goal",
            ["lose_weight", "maintain", "gain_weight", "build_muscle"],
            index=["lose_weight","maintain","gain_weight","build_muscle"].index(
                profile.goal) if profile else 1)
        restrictions = st.text_input("Dietary Restrictions (comma-sep)",
            value=profile.dietary_restrictions if profile else "")
        allergies = st.text_input("Allergies",
            value=profile.allergies if profile else "")

        if st.button("💾 Save Profile", use_container_width=True):
            targets = compute_targets(age, gender, height, weight, activity, goal)
            if not profile:
                profile = UserProfile(name=st.session_state.username)
                session.add(profile)
            profile.age = age; profile.gender = gender
            profile.height_cm = height; profile.weight_kg = weight
            profile.activity_level = activity; profile.goal = goal
            profile.dietary_restrictions = restrictions
            profile.allergies = allergies
            profile.target_calories = targets["target_calories"]
            profile.target_protein = targets["target_protein"]
            profile.target_carbs = targets["target_carbs"]
            profile.target_fat = targets["target_fat"]
            session.commit()
            st.success("Profile saved!")
            st.rerun()

    if profile:
        st.markdown("### 🎯 Daily Targets")
        st.metric("Calories", f"{profile.target_calories} kcal")
        
        # Fixed Sidebar UI to prevent cutoff
        st.markdown(f"""
        **Daily Macros:**
        * 🥩 **Protein:** {profile.target_protein}g
        * 🍞 **Carbs:** {profile.target_carbs}g
        * 🥑 **Fat:** {profile.target_fat}g
        """)

        st.markdown("### ⚖️ Quick Weight Log")
        new_w = st.number_input("Weight kg", 30.0, 300.0, profile.weight_kg, key="qw")
        if st.button("Log Weight"):
            session.add(WeightLog(weight_kg=new_w, username=st.session_state.username))
            profile.weight_kg = new_w
            session.commit()
            st.success(f"Logged {new_w} kg")
            st.rerun()

    session.close()

# ---------- MAIN HEADER ----------
st.markdown('<p class="main-header">🥗 AI Diet Coach Dashboard</p>', unsafe_allow_html=True)
st.caption("Your personal multi-agent nutrition assistant powered by LangGraph")

if not profile:
    st.warning("👈 Please create your profile in the sidebar to begin.")
    st.stop()

# ---------- TABS ----------
tab1, tab2, tab3, tab4 = st.tabs(["📊 Today", "📈 Trends", "🍽️ Meal Log", "🤖 Chat with Agent"])

# ========== TAB 1: TODAY ==========
with tab1:
    session = get_session()
    today = datetime.utcnow().date()
    start = datetime.combine(today, datetime.min.time())
    meals_today = session.query(MealLog).filter(
        MealLog.username == st.session_state.username,
        MealLog.date >= start
    ).all()

    totals = {"calories": 0, "protein": 0, "carbs": 0, "fat": 0, "fiber": 0}
    for m in meals_today:
        totals["calories"] += m.calories; totals["protein"] += m.protein
        totals["carbs"] += m.carbs; totals["fat"] += m.fat; totals["fiber"] += m.fiber

    st.subheader(f"📅 {today.strftime('%A, %B %d, %Y')}")

    # Progress rings
    col1, col2, col3, col4 = st.columns(4)
    def progress_gauge(value, target, label, color):
        pct = min(value / target * 100, 100) if target else 0
        fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=value,
            number={'suffix': f" / {target}"},
            title={'text': label},
            gauge={'axis': {'range': [0, target * 1.2]},
                   'bar': {'color': color},
                   'threshold': {'line': {'color': "red", 'width': 3},
                                 'thickness': 0.75, 'value': target}},
        ))
        fig.update_layout(height=200, margin=dict(l=10, r=10, t=40, b=10))
        return fig

    with col1:
        st.plotly_chart(progress_gauge(totals["calories"], profile.target_calories,
                        "Calories", "#38ef7d"), use_container_width=True)
    with col2:
        st.plotly_chart(progress_gauge(totals["protein"], profile.target_protein,
                        "Protein (g)", "#ff6b6b"), use_container_width=True)
    with col3:
        st.plotly_chart(progress_gauge(totals["carbs"], profile.target_carbs,
                        "Carbs (g)", "#feca57"), use_container_width=True)
    with col4:
        st.plotly_chart(progress_gauge(totals["fat"], profile.target_fat,
                        "Fat (g)", "#a29bfe"), use_container_width=True)

    # Macro split pie
    colA, colB = st.columns([1, 1])
    with colA:
        st.markdown("#### 🥧 Macro Distribution Today")
        if totals["protein"] + totals["carbs"] + totals["fat"] > 0:
            pie = px.pie(
                names=["Protein", "Carbs", "Fat"],
                values=[totals["protein"]*4, totals["carbs"]*4, totals["fat"]*9],
                color_discrete_sequence=["#ff6b6b", "#feca57", "#a29bfe"],
                hole=0.5
            )
            pie.update_layout(height=320)
            st.plotly_chart(pie, use_container_width=True)
        else:
            st.info("No meals logged yet today.")

    with colB:
        st.markdown("#### 🍴 Meals Breakdown")
        by_type = {"breakfast": 0, "lunch": 0, "dinner": 0, "snack": 0}
        for m in meals_today:
            by_type[m.meal_type] = by_type.get(m.meal_type, 0) + m.calories
        bar = px.bar(x=list(by_type.keys()), y=list(by_type.values()),
                     labels={"x": "Meal", "y": "Calories"},
                     color=list(by_type.keys()),
                     color_discrete_sequence=px.colors.sequential.Teal)
        bar.update_layout(height=320, showlegend=False)
        st.plotly_chart(bar, use_container_width=True)

    session.close()

# ========== TAB 2: TRENDS ==========
with tab2:
    session = get_session()
    st.subheader("📈 7-Day Trends")

    days = []
    for d in range(6, -1, -1):
        dt = datetime.utcnow().date() - timedelta(days=d)
        s = datetime.combine(dt, datetime.min.time())
        e = s + timedelta(days=1)
        ms = session.query(MealLog).filter(
            MealLog.username == st.session_state.username,
            MealLog.date >= s, MealLog.date < e
        ).all()
        days.append({
            "date": dt.strftime("%a %m/%d"),
            "calories": sum(m.calories for m in ms),
            "protein": sum(m.protein for m in ms),
            "carbs": sum(m.carbs for m in ms),
            "fat": sum(m.fat for m in ms),
        })
    df = pd.DataFrame(days)

    fig = go.Figure()
    fig.add_trace(go.Bar(x=df["date"], y=df["calories"], name="Calories", marker_color="#38ef7d"))
    fig.add_hline(y=profile.target_calories, line_dash="dash", line_color="red",
                  annotation_text=f"Target {profile.target_calories}")
    fig.update_layout(title="Daily Calories vs Target", height=350)
    st.plotly_chart(fig, use_container_width=True)

    # Macro stacked
    fig2 = go.Figure()
    fig2.add_trace(go.Bar(x=df["date"], y=df["protein"], name="Protein", marker_color="#ff6b6b"))
    fig2.add_trace(go.Bar(x=df["date"], y=df["carbs"], name="Carbs", marker_color="#feca57"))
    fig2.add_trace(go.Bar(x=df["date"], y=df["fat"], name="Fat", marker_color="#a29bfe"))
    fig2.update_layout(barmode="stack", title="Daily Macros (grams)", height=350)
    st.plotly_chart(fig2, use_container_width=True)

    # Weight chart
    weights = session.query(WeightLog).filter(
        WeightLog.username == st.session_state.username
    ).order_by(WeightLog.date).all()
    
    if weights:
        wdf = pd.DataFrame([{"date": w.date, "weight": w.weight_kg} for w in weights])
        wfig = px.line(wdf, x="date", y="weight", markers=True,
                       title="Weight Progress", color_discrete_sequence=["#38ef7d"])
        wfig.update_layout(height=300)
        st.plotly_chart(wfig, use_container_width=True)
    session.close()

# ========== TAB 3: MEAL LOG ==========
with tab3:
    session = get_session()
    st.subheader("🍽️ Recent Meals")
    recent = session.query(MealLog).filter(
        MealLog.username == st.session_state.username
    ).order_by(MealLog.date.desc()).limit(50).all()
    
    if recent:
        df = pd.DataFrame([{
            "Date": m.date.strftime("%Y-%m-%d %H:%M"),
            "Meal": m.meal_type.capitalize(),
            "Food": m.food_name,
            "Qty (g)": m.quantity_g,
            "Kcal": m.calories,
            "P": m.protein, "C": m.carbs, "F": m.fat,
        } for m in recent])
        st.dataframe(df, use_container_width=True, hide_index=True)

        if st.button("🗑️ Clear My Logs (debug)"):
            session.query(MealLog).filter(MealLog.username == st.session_state.username).delete()
            session.commit()
            st.rerun()
    else:
        st.info("No meals logged yet. Use the Chat tab to log meals naturally!")
    session.close()

# ========== TAB 4: CHAT ==========
with tab4:
    st.subheader("🤖 Chat with Your AI Diet Agent")
    st.caption("Try: *'Log 150g grilled chicken for lunch'* · *'Plan my dinner'* · *'How am I doing this week?'*")

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
        st.session_state.lc_history = []

    # Display history
    for role, content, intent in st.session_state.chat_history:
        with st.chat_message(role):
            if role == "assistant" and intent:
                st.caption(f"🧠 Routed to: **{intent}** agent")
            st.markdown(content)

    if prompt := st.chat_input("Ask your diet agent anything..."):
        st.session_state.chat_history.append(("user", prompt, None))
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("🧠 Agents thinking..."):
                try:
                    # Keep last 6 messages as context
                    reply, intent, full_msgs = run_agent(
                        prompt, st.session_state.lc_history[-6:]
                    )
                    st.caption(f"🧠 Routed to: **{intent}** agent")
                    st.markdown(reply)
                    st.session_state.chat_history.append(("assistant", reply, intent))
                    # Update lc_history
                    st.session_state.lc_history.append(HumanMessage(content=prompt))
                    st.session_state.lc_history.append(AIMessage(content=reply))
                except Exception as e:
                    st.error(f"Agent error: {e}")

    col1, col2 = st.columns([1, 5])
    if col1.button("🔄 New Chat"):
        st.session_state.chat_history = []
        st.session_state.lc_history = []
        st.rerun()