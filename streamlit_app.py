import streamlit as st
import requests
from dataclasses import dataclass
from typing import Optional, Any
from datetime import datetime, timedelta
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# ── Boli Auctions Python SDK ──

@dataclass
class RateLimit:
    limit: int
    remaining: int
    reset: int

class BoliClient:
    """Enterprise client for the Boli Auctions API."""

    def __init__(self, api_key: str, base_url: str = "https://dcobznuyvfgeskkjbwdf.supabase.co/functions/v1/api-gateway"):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            "x-api-key": api_key,
            "Content-Type": "application/json",
        })
        self.rate_limit: Optional[RateLimit] = None

    def _request(self, method: str, path: str, json: Any = None) -> dict:
        r = self.session.request(method, f"{self.base_url}{path}", json=json)
        self.rate_limit = RateLimit(
            limit=int(r.headers.get("X-RateLimit-Limit", 100)),
            remaining=int(r.headers.get("X-RateLimit-Remaining", 0)),
            reset=int(r.headers.get("X-RateLimit-Reset", 0)),
        )
        r.raise_for_status()
        return r.json()

    # ── Auctions ──
    def list_auctions(self) -> list:
        return self._request("GET", "/auctions")["auctions"]

    def create_auction(self, title: str, auction_type: str = "english",
                       is_public: bool = True, **kwargs) -> dict:
        return self._request("POST", "/auctions", json={
            "title": title, "auction_type": auction_type,
            "is_public": is_public, **kwargs
        })["auction"]

    def get_auction(self, auction_id: str) -> dict:
        return self._request("GET", f"/auctions/{auction_id}")["auction"]

    def update_auction(self, auction_id: str, **kwargs) -> dict:
        return self._request("PATCH", f"/auctions/{auction_id}", json=kwargs)["auction"]

    def delete_auction(self, auction_id: str) -> dict:
        return self._request("DELETE", f"/auctions/{auction_id}")

    # ── Items ──
    def list_items(self, auction_id: str) -> list:
        return self._request("GET", f"/auctions/{auction_id}/items")["items"]

    def add_item(self, auction_id: str, name: str, starting_price: float = 0, **kwargs) -> dict:
        return self._request("POST", f"/auctions/{auction_id}/items", json={
            "name": name, "starting_price": starting_price, **kwargs
        })["item"]

    def update_item(self, auction_id: str, item_id: str, **kwargs) -> dict:
        return self._request("PATCH", f"/auctions/{auction_id}/items/{item_id}", json=kwargs)["item"]

    def delete_item(self, auction_id: str, item_id: str) -> dict:
        return self._request("DELETE", f"/auctions/{auction_id}/items/{item_id}")

    # ── Bids & Participants ──
    def list_bids(self, auction_id: str) -> list:
        return self._request("GET", f"/auctions/{auction_id}/bids")["bids"]

    def list_participants(self, auction_id: str) -> list:
        return self._request("GET", f"/auctions/{auction_id}/participants")["participants"]

    def invite_participant(self, auction_id: str, user_id: str) -> dict:
        return self._request("POST", f"/auctions/{auction_id}/participants",
                             json={"user_id": user_id})["participant"]

    # ── Results & Audit ──
    def get_results(self, auction_id: str) -> dict:
        return self._request("GET", f"/auctions/{auction_id}/results")

    def get_audit_logs(self, auction_id: str) -> list:
        return self._request("GET", f"/auctions/{auction_id}/audit-logs")["logs"]


# ── Streamlit App Configuration ──

st.set_page_config(
    page_title="Boli Auctions Manager",
    page_icon="🔨",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .stMetric {
        background-color: #f0f2f6;
        padding: 15px;
        border-radius: 5px;
    }
    .success-box {
        padding: 10px;
        background-color: #d4edda;
        border-left: 5px solid #28a745;
        margin: 10px 0;
    }
    .error-box {
        padding: 10px;
        background-color: #f8d7da;
        border-left: 5px solid #dc3545;
        margin: 10px 0;
    }
    .info-box {
        padding: 10px;
        background-color: #d1ecf1;
        border-left: 5px solid #17a2b8;
        margin: 10px 0;
    }
</style>
""", unsafe_allow_html=True)

# ── Initialize Client ──

@st.cache_resource
def get_client():
    """Initialize Boli client with credentials from Streamlit secrets."""
    try:
        api_key = st.secrets["boli"]["api_key"]
        base_url = st.secrets.get("boli", {}).get("base_url", "https://dcobznuyvfgeskkjbwdf.supabase.co/functions/v1/api-gateway")
        return BoliClient(api_key, base_url)
    except Exception as e:
        st.error(f"Failed to initialize client: {str(e)}")
        st.info("Please configure your secrets.toml file with:\n\n[boli]\napi_key = \"your_api_key_here\"")
        st.stop()

client = get_client()

# ── Sidebar Navigation ──

st.sidebar.title("🔨 Boli Auctions")
st.sidebar.markdown("---")

page = st.sidebar.radio(
    "Navigation",
    ["📊 Dashboard", "🎯 Auctions", "📦 Items", "💰 Bids & Results", "👥 Participants", "📜 Audit Logs"]
)

# Display rate limit info
if client.rate_limit:
    st.sidebar.markdown("---")
    st.sidebar.metric("API Rate Limit", f"{client.rate_limit.remaining}/{client.rate_limit.limit}")

st.sidebar.markdown("---")
st.sidebar.caption("Boli Auctions Manager v1.0")

# ── Helper Functions ──

def format_datetime(dt_string):
    """Format datetime string for display."""
    if not dt_string:
        return "Not set"
    try:
        dt = datetime.fromisoformat(dt_string.replace('Z', '+00:00'))
        return dt.strftime("%Y-%m-%d %H:%M UTC")
    except:
        return dt_string

def get_status_color(status):
    """Return color based on auction status."""
    colors = {
        "draft": "🟡",
        "live": "🟢",
        "ended": "🔴",
        "cancelled": "⚫"
    }
    return colors.get(status, "⚪")

# ── Page: Dashboard ──

if page == "📊 Dashboard":
    st.title("📊 Auction Dashboard")
    
    try:
        auctions = client.list_auctions()
        
        # Summary metrics
        col1, col2, col3, col4 = st.columns(4)
        
        total_auctions = len(auctions)
        live_auctions = len([a for a in auctions if a.get("status") == "live"])
        draft_auctions = len([a for a in auctions if a.get("status") == "draft"])
        ended_auctions = len([a for a in auctions if a.get("status") == "ended"])
        
        col1.metric("Total Auctions", total_auctions)
        col2.metric("Live Auctions", live_auctions, delta="Active")
        col3.metric("Draft Auctions", draft_auctions)
        col4.metric("Ended Auctions", ended_auctions)
        
        st.markdown("---")
        
        if auctions:
            # Auction status distribution
            col1, col2 = st.columns([1, 1])
            
            with col1:
                st.subheader("Auction Status Distribution")
                status_counts = pd.DataFrame(auctions)['status'].value_counts()
                fig = px.pie(
                    values=status_counts.values,
                    names=status_counts.index,
                    title="Auctions by Status",
                    color_discrete_sequence=px.colors.qualitative.Set3
                )
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                st.subheader("Auction Types")
                type_counts = pd.DataFrame(auctions)['auction_type'].value_counts()
                fig = px.bar(
                    x=type_counts.index,
                    y=type_counts.values,
                    title="Auctions by Type",
                    labels={'x': 'Type', 'y': 'Count'},
                    color_discrete_sequence=['#1f77b4']
                )
                st.plotly_chart(fig, use_container_width=True)
            
            # Recent auctions
            st.subheader("Recent Auctions")
            df = pd.DataFrame(auctions)
            display_cols = ['title', 'auction_type', 'status', 'is_public', 'created_at']
            available_cols = [col for col in display_cols if col in df.columns]
            
            if available_cols:
                st.dataframe(
                    df[available_cols].head(10),
                    use_container_width=True,
                    hide_index=True
                )
        else:
            st.info("No auctions found. Create your first auction to get started!")
            
    except Exception as e:
        st.error(f"Error loading dashboard: {str(e)}")

# ── Page: Auctions ──

elif page == "🎯 Auctions":
    st.title("🎯 Auction Management")
    
    tab1, tab2, tab3 = st.tabs(["📋 List Auctions", "➕ Create Auction", "✏️ Manage Auction"])
    
    with tab1:
        st.subheader("All Auctions")
        
        try:
            auctions = client.list_auctions()
            
            if auctions:
                for auction in auctions:
                    with st.expander(f"{get_status_color(auction.get('status', 'draft'))} {auction['title']} - {auction['id']}"):
                        col1, col2, col3 = st.columns(3)
                        
                        col1.write(f"**Type:** {auction.get('auction_type', 'N/A')}")
                        col1.write(f"**Status:** {auction.get('status', 'N/A')}")
                        col1.write(f"**Public:** {'Yes' if auction.get('is_public') else 'No'}")
                        
                        col2.write(f"**Start:** {format_datetime(auction.get('start_time'))}")
                        col2.write(f"**End:** {format_datetime(auction.get('end_time'))}")
                        col2.write(f"**Created:** {format_datetime(auction.get('created_at'))}")
                        
                        if auction.get('description'):
                            col3.write(f"**Description:** {auction['description']}")
                        
                        st.json(auction)
            else:
                st.info("No auctions found.")
                
        except Exception as e:
            st.error(f"Error loading auctions: {str(e)}")
    
    with tab2:
        st.subheader("Create New Auction")
        
        with st.form("create_auction_form"):
            title = st.text_input("Auction Title*", placeholder="e.g., Art Collection Sale")
            
            col1, col2 = st.columns(2)
            
            with col1:
                auction_type = st.selectbox(
                    "Auction Type*",
                    ["english", "dutch", "sealed_bid", "reverse"]
                )
                is_public = st.checkbox("Public Auction", value=True)
            
            with col2:
                start_time = st.datetime_input(
                    "Start Time",
                    value=datetime.now() + timedelta(days=1)
                )
                end_time = st.datetime_input(
                    "End Time",
                    value=datetime.now() + timedelta(days=2)
                )
            
            description = st.text_area("Description", placeholder="Enter auction description...")
            
            submit = st.form_submit_button("Create Auction", type="primary")
            
            if submit:
                if not title:
                    st.error("Please provide a title")
                else:
                    try:
                        auction_data = {
                            "title": title,
                            "auction_type": auction_type,
                            "is_public": is_public,
                            "start_time": start_time.isoformat() + "Z",
                            "end_time": end_time.isoformat() + "Z",
                        }
                        
                        if description:
                            auction_data["description"] = description
                        
                        auction = client.create_auction(**auction_data)
                        st.success(f"✅ Auction created successfully! ID: {auction['id']}")
                        st.json(auction)
                        st.rerun()
                        
                    except Exception as e:
                        st.error(f"Error creating auction: {str(e)}")
    
    with tab3:
        st.subheader("Manage Existing Auction")
        
        try:
            auctions = client.list_auctions()
            
            if auctions:
                auction_options = {f"{a['title']} ({a['id']})": a['id'] for a in auctions}
                selected = st.selectbox("Select Auction", options=list(auction_options.keys()))
                
                if selected:
                    auction_id = auction_options[selected]
                    auction = client.get_auction(auction_id)
                    
                    st.json(auction)
                    
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        if st.button("🟢 Set to Live", use_container_width=True):
                            try:
                                client.update_auction(auction_id, status="live")
                                st.success("Auction is now live!")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error: {str(e)}")
                    
                    with col2:
                        if st.button("🔴 End Auction", use_container_width=True):
                            try:
                                client.update_auction(auction_id, status="ended")
                                st.success("Auction ended!")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error: {str(e)}")
                    
                    with col3:
                        if st.button("🗑️ Delete Auction", use_container_width=True, type="secondary"):
                            try:
                                client.delete_auction(auction_id)
                                st.success("Auction deleted!")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error: {str(e)}")
            else:
                st.info("No auctions available to manage.")
                
        except Exception as e:
            st.error(f"Error: {str(e)}")

# ── Page: Items ──

elif page == "📦 Items":
    st.title("📦 Item Management")
    
    try:
        auctions = client.list_auctions()
        
        if not auctions:
            st.info("No auctions found. Create an auction first.")
        else:
            auction_options = {f"{a['title']} ({a['id']})": a['id'] for a in auctions}
            selected = st.selectbox("Select Auction", options=list(auction_options.keys()))
            
            if selected:
                auction_id = auction_options[selected]
                
                tab1, tab2 = st.tabs(["📋 View Items", "➕ Add Item"])
                
                with tab1:
                    st.subheader("Auction Items")
                    
                    try:
                        items = client.list_items(auction_id)
                        
                        if items:
                            for item in items:
                                with st.expander(f"{item['name']} - ${item.get('starting_price', 0):,.2f}"):
                                    col1, col2 = st.columns([2, 1])
                                    
                                    with col1:
                                        st.write(f"**Item ID:** {item['id']}")
                                        st.write(f"**Starting Price:** ${item.get('starting_price', 0):,.2f}")
                                        if item.get('description'):
                                            st.write(f"**Description:** {item['description']}")
                                        if item.get('current_bid'):
                                            st.write(f"**Current Bid:** ${item['current_bid']:,.2f}")
                                    
                                    with col2:
                                        if st.button(f"Delete", key=f"del_{item['id']}"):
                                            try:
                                                client.delete_item(auction_id, item['id'])
                                                st.success("Item deleted!")
                                                st.rerun()
                                            except Exception as e:
                                                st.error(f"Error: {str(e)}")
                        else:
                            st.info("No items in this auction yet.")
                            
                    except Exception as e:
                        st.error(f"Error loading items: {str(e)}")
                
                with tab2:
                    st.subheader("Add New Item")
                    
                    with st.form("add_item_form"):
                        name = st.text_input("Item Name*", placeholder="e.g., Oil Painting - Sunset")
                        starting_price = st.number_input("Starting Price*", min_value=0.0, value=100.0, step=10.0)
                        description = st.text_area("Description", placeholder="Item description...")
                        
                        submit = st.form_submit_button("Add Item", type="primary")
                        
                        if submit:
                            if not name:
                                st.error("Please provide an item name")
                            else:
                                try:
                                    item_data = {
                                        "name": name,
                                        "starting_price": starting_price
                                    }
                                    
                                    if description:
                                        item_data["description"] = description
                                    
                                    item = client.add_item(auction_id, **item_data)
                                    st.success(f"✅ Item added successfully! ID: {item['id']}")
                                    st.json(item)
                                    st.rerun()
                                    
                                except Exception as e:
                                    st.error(f"Error adding item: {str(e)}")
    
    except Exception as e:
        st.error(f"Error: {str(e)}")

# ── Page: Bids & Results ──

elif page == "💰 Bids & Results":
    st.title("💰 Bids & Auction Results")
    
    try:
        auctions = client.list_auctions()
        
        if not auctions:
            st.info("No auctions found.")
        else:
            auction_options = {f"{a['title']} ({a['id']})": a['id'] for a in auctions}
            selected = st.selectbox("Select Auction", options=list(auction_options.keys()))
            
            if selected:
                auction_id = auction_options[selected]
                
                tab1, tab2 = st.tabs(["💰 Bids", "📊 Results"])
                
                with tab1:
                    st.subheader("Auction Bids")
                    
                    try:
                        bids = client.list_bids(auction_id)
                        
                        if bids:
                            df = pd.DataFrame(bids)
                            st.dataframe(df, use_container_width=True, hide_index=True)
                            
                            # Bid visualization
                            if 'amount' in df.columns and 'created_at' in df.columns:
                                st.subheader("Bid History")
                                fig = px.line(
                                    df,
                                    x='created_at',
                                    y='amount',
                                    title='Bid Progression Over Time',
                                    markers=True
                                )
                                st.plotly_chart(fig, use_container_width=True)
                        else:
                            st.info("No bids placed yet.")
                            
                    except Exception as e:
                        st.error(f"Error loading bids: {str(e)}")
                
                with tab2:
                    st.subheader("Auction Results")
                    
                    try:
                        results = client.get_results(auction_id)
                        
                        if results:
                            # Summary metrics
                            if 'summary' in results:
                                summary = results['summary']
                                col1, col2, col3, col4 = st.columns(4)
                                
                                col1.metric(
                                    "Total Revenue",
                                    f"${summary.get('total_revenue', 0):,.2f}"
                                )
                                col2.metric(
                                    "Total Bids",
                                    summary.get('total_bids', 0)
                                )
                                col3.metric(
                                    "Unique Bidders",
                                    summary.get('unique_bidders', 0)
                                )
                                col4.metric(
                                    "Items Sold",
                                    summary.get('items_sold', 0)
                                )
                            
                            st.markdown("---")
                            st.json(results)
                        else:
                            st.info("No results available yet.")
                            
                    except Exception as e:
                        st.error(f"Error loading results: {str(e)}")
    
    except Exception as e:
        st.error(f"Error: {str(e)}")

# ── Page: Participants ──

elif page == "👥 Participants":
    st.title("👥 Participant Management")
    
    try:
        auctions = client.list_auctions()
        
        if not auctions:
            st.info("No auctions found.")
        else:
            auction_options = {f"{a['title']} ({a['id']})": a['id'] for a in auctions}
            selected = st.selectbox("Select Auction", options=list(auction_options.keys()))
            
            if selected:
                auction_id = auction_options[selected]
                
                tab1, tab2 = st.tabs(["📋 View Participants", "➕ Invite Participant"])
                
                with tab1:
                    st.subheader("Auction Participants")
                    
                    try:
                        participants = client.list_participants(auction_id)
                        
                        if participants:
                            df = pd.DataFrame(participants)
                            st.dataframe(df, use_container_width=True, hide_index=True)
                        else:
                            st.info("No participants yet.")
                            
                    except Exception as e:
                        st.error(f"Error loading participants: {str(e)}")
                
                with tab2:
                    st.subheader("Invite New Participant")
                    
                    with st.form("invite_participant_form"):
                        user_id = st.text_input("User ID*", placeholder="Enter user ID to invite")
                        
                        submit = st.form_submit_button("Send Invitation", type="primary")
                        
                        if submit:
                            if not user_id:
                                st.error("Please provide a user ID")
                            else:
                                try:
                                    participant = client.invite_participant(auction_id, user_id)
                                    st.success(f"✅ Invitation sent successfully!")
                                    st.json(participant)
                                    st.rerun()
                                    
                                except Exception as e:
                                    st.error(f"Error inviting participant: {str(e)}")
    
    except Exception as e:
        st.error(f"Error: {str(e)}")

# ── Page: Audit Logs ──

elif page == "📜 Audit Logs":
    st.title("📜 Audit Logs")
    
    try:
        auctions = client.list_auctions()
        
        if not auctions:
            st.info("No auctions found.")
        else:
            auction_options = {f"{a['title']} ({a['id']})": a['id'] for a in auctions}
            selected = st.selectbox("Select Auction", options=list(auction_options.keys()))
            
            if selected:
                auction_id = auction_options[selected]
                
                try:
                    logs = client.get_audit_logs(auction_id)
                    
                    if logs:
                        st.info(f"Found {len(logs)} audit log entries")
                        
                        # Display as expandable items
                        for i, log in enumerate(logs):
                            timestamp = format_datetime(log.get('timestamp', log.get('created_at', '')))
                            action = log.get('action', 'Unknown')
                            
                            with st.expander(f"{i+1}. {action} - {timestamp}"):
                                st.json(log)
                        
                        # Also show as dataframe
                        st.subheader("Log Table")
                        df = pd.DataFrame(logs)
                        st.dataframe(df, use_container_width=True, hide_index=True)
                    else:
                        st.info("No audit logs found for this auction.")
                        
                except Exception as e:
                    st.error(f"Error loading audit logs: {str(e)}")
    
    except Exception as e:
        st.error(f"Error: {str(e)}")
