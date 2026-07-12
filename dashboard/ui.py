import streamlit as st
import requests
import json

API_URL = "http://localhost:8000"

st.set_page_config(page_title="Virelo AI", page_icon="🚀", layout="wide")


if "token" not in st.session_state:
    st.title("🚀 Virelo AI")
    st.subheader("AI-powered social media automation")

    tab_login, tab_register = st.tabs(["Login", "Register"])

    with tab_login:
        email    = st.text_input("Email", key="login_email")
        password = st.text_input("Password", type="password", key="login_pass")

        if st.button("Login", use_container_width=True, type="primary"):
            response = requests.post(f"{API_URL}/auth/login", json={
                "email": email, "password": password
            })
            if response.status_code == 200:
                data = response.json()
                st.session_state["token"]   = data["access_token"]
                st.session_state["user_id"] = data["user_id"]
                st.rerun()
            else:
                st.error("Invalid email or password")

    with tab_register:
        username = st.text_input("Username", key="reg_username")
        email    = st.text_input("Email", key="reg_email")
        password = st.text_input("Password", type="password", key="reg_pass")

        if st.button("Register", use_container_width=True, type="primary"):
            response = requests.post(f"{API_URL}/auth/register", json={
                "username": username,
                "email":    email,
                "password": password
            })
            if response.status_code == 200:
                data = response.json()
                st.session_state["token"]   = data["access_token"]
                st.session_state["user_id"] = data["user_id"]
                st.rerun()
            else:
                st.error(response.json().get("detail", "Registration failed"))

    st.stop() 

headers = {"Authorization": f"Bearer {st.session_state['token']}"}

with st.sidebar:
    st.title("🚀 Virelo AI")
    st.caption(f"User ID: {st.session_state['user_id']}")

    if st.button("Logout"):
        st.session_state.clear()
        st.rerun()

    st.divider()
    st.subheader("Connect Accounts")

    user_id = st.session_state["user_id"]
    token   = st.session_state["token"]

    twitter_url = f"{API_URL}/oauth/twitter/connect?token={token}"
    st.markdown(
        f'<a href="{twitter_url}" target="_self" style="'
        f'display:block; padding:8px 16px; background:#1DA1F2; '
        f'color:white; border-radius:8px; text-decoration:none; '
        f'text-align:center; margin-bottom:8px;">🐦 Connect Twitter</a>',
        unsafe_allow_html=True
    )

    linkedin_url = f"{API_URL}/oauth/linkedin/connect?token={token}"
    st.markdown(
        f'<a href="{linkedin_url}" target="_self" style="'
        f'display:block; padding:8px 16px; background:#0077B5; '
        f'color:white; border-radius:8px; text-decoration:none; '
        f'text-align:center; margin-bottom:8px;">💼 Connect LinkedIn</a>',
        unsafe_allow_html=True
    )

    st.divider()

    st.subheader("Connection Status")
    try:
        for platform in ["twitter","linkedin"]:
            r = requests.get(
                f"{API_URL}/accounts/connect/{user_id}/{platform}",
                headers={"Authorization": f"Bearer {token}"}
            )
            if r.status_code == 200:
                st.success(f"✅ {platform.title()} connected")
            else:
                st.error(f"❌ {platform.title()} not connected")
    except:
        pass

tab1, tab2, tab3 = st.tabs(["✍️ Generate", "📅 Scheduled", "📊 Analytics"])

with tab1:
    st.header("Generate Content")

    user_query = st.text_area(
        "What do you want to post about?",
        placeholder="e.g. AI trends in fintech",
        height=100
    )

    col1, col2 = st.columns(2)
    with col1:
        platforms = st.multiselect(
            "Target Platforms",
            ["twitter","linkedin"],
            default=["twitter"]
        )
    with col2:
        schedule_time = st.text_input(
            "Schedule (optional)",
            placeholder="2025-01-15 09:00"
        )

    if st.button("🚀 Generate", use_container_width=True, type="primary"):
        if not user_query:
            st.error("Enter a topic first")
        elif not platforms:
            st.error("Select at least one platform")
        else:
            with st.spinner("Generating... (30-60 seconds)"):
                try:
                    response = requests.post(
                        f"{API_URL}/posts/generate",
                        json={
                            "user_id":          st.session_state["user_id"],
                            "user_query":       user_query,
                            "target_platforms": platforms,
                            "schedule_time":    schedule_time or None
                        },
                        headers=headers,
                        timeout=120
                    )
                    if response.status_code == 200:
                        data = response.json()
                        st.session_state["draft_posts"] = data.get("draft_posts", {})
                        st.session_state["post_status"] = data.get("status")
                        st.success("Content generated!")
                    else:
                        st.error(f"Error: {response.text}")
                except Exception as e:
                    st.error(str(e))


    if st.session_state.get("post_status") == "pending_approval":
        st.divider()
        st.subheader("Review Content")
        draft = st.session_state.get("draft_posts", {})

        if "twitter" in draft:
            with st.expander("Twitter Thread", expanded=True):
                try:
                    tweets = json.loads(draft["twitter"])
                    for i, tweet in enumerate(tweets):
                        st.markdown(f"**Tweet {i+1}** ({len(tweet)}/280)")
                        st.text_area(f"t{i}", tweet, height=80,
                                     label_visibility="collapsed")
                except:
                    st.write(draft["twitter"])


        if "linkedin" in draft:
            with st.expander("LinkedIn", expanded=True):
                st.text_area("li", draft["linkedin"], height=150,
                             label_visibility="collapsed")

        st.divider()
        col1, col2, col3 = st.columns(3)

        with col1:
            if st.button("Approve", use_container_width=True, type="primary"):
                with st.spinner("Publishing..."):
                    r = requests.post(
                        f"{API_URL}/posts/approve",
                        params={"user_id": st.session_state["user_id"],
                                "choice": "approve"},
                        headers=headers, timeout=60
                    )
                    if r.status_code == 200:
                        data = r.json()
                        st.session_state["post_status"]    = "complete"
                        st.session_state["publish_results"] = data.get("publish_results", {})
                        st.rerun()
                    else:
                        st.error(r.text)

        with col2:
            if st.button("Regenerate", use_container_width=True):
                with st.spinner("Regenerating..."):
                    r = requests.post(
                        f"{API_URL}/posts/approve",
                        params={"user_id": st.session_state["user_id"],
                                "choice": "regenerate"},
                        headers=headers, timeout=120
                    )
                    if r.status_code == 200:
                        data = r.json()
                        st.session_state["draft_posts"] = data.get("draft_posts", {})
                        st.session_state["post_status"] = data.get("status")
                        st.rerun()

        with col3:
            if st.button("Reject", use_container_width=True):
                requests.post(
                    f"{API_URL}/posts/approve",
                    params={"user_id": st.session_state["user_id"],
                            "choice": "reject"},
                    headers=headers
                )
                st.session_state["post_status"] = None
                st.session_state["draft_posts"] = {}
                st.rerun()

    if st.session_state.get("post_status") == "complete":
        st.divider()
        st.subheader("Published!")
        for platform, result in st.session_state.get("publish_results", {}).items():
            st.success(f"{platform.title()}: {result}")

with tab2:
    st.header("Scheduled Posts")
    if st.button("Refresh"):
        st.rerun()
    try:
        r = requests.get(f"{API_URL}/posts/scheduled",
                         headers=headers, timeout=10)
        posts = r.json().get("scheduled_posts", [])
        if not posts:
            st.info("No scheduled posts")
        for post in posts:
            col1, col2, col3 = st.columns([3, 1, 1])
            with col1:
                st.write(f"**{post['platform'].title()}**")
                st.caption(str(post.get("caption", ""))[:100])
            with col2:
                st.write(post.get("scheduled_time", ""))
            with col3:
                s = post.get("status", "")
                if s == "pending":
                    st.warning(s)
                elif s == "posted":
                    st.success(s)
                else:
                    st.error(s)
            st.divider()
    except Exception as e:
        st.error(str(e))

with tab3:
    st.header("Analytics")
    st.info("Connect accounts and start posting to see analytics")