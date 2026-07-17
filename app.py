import streamlit as st
import pandas as pd
from streamlit_option_menu import option_menu
import plotly.express as px


st.set_page_config(page_title="Uber Analytics",layout="wide")

# LOAD DATASET

@st.cache_data
def load_data():
     df = pd.read_csv("uber.csv")
     return df
df = load_data()

# SIDEBAR MENU

with st.sidebar:
    selected = option_menu("Main Menu",["Dataset",
                                        "Overview","Ride Analytics","Data Assistant","Dashboard"],
                           icons=["table","bar-chart","graph-up","robot","bar-chart"],
                           menu_icon="car-front",default_index=0)

if selected == "Dataset":
    st.title("Dataset Explorer")
    st.divider()

    # DATASET OVERVIEW

    col1 ,col2 , col3 = st.columns(3)

    col1.metric("Total Rows",df.shape[0])
    col2.metric("Total Columns",df.shape[1])
    col3.metric("Missing Value",df.isna().sum().sum())

    st.divider()

    # COLUMNS SECTION
    st.subheader("Select Columns")
    selected_columns = st.multiselect("Choose columns to display",
                                      df.columns,default=df.columns)
    filtered_df = df[selected_columns]

    # SEARCH DATASET

    st.subheader("Search in Dataset")
    search_value = st.text_input("Search Any Value")
    if search_value:
        filtered_df = filtered_df[filtered_df.astype(str).apply(
            lambda row:row.str.contains(search_value,case=False).any(),axis=1)]

    # COLUMN FILTER
    st.subheader("Column Filter")

    col1 , col2 = st.columns(2)

    with col1:
        filter_column = st.selectbox("Select Column",filtered_df.columns)
    with col2:
        filter_value = st.selectbox("Select Value",filtered_df[filter_column].dropna().unique())

    if st.button("Apply Filter"):
        filtered_df = filtered_df[filtered_df[filter_column]==filter_value]
    st.divider()

    # ROW DISPLAY

    st.subheader("Row Display")

    row = st.slider("Number of rows to display",10,len(filtered_df),100)
    st.divider()

    # DATASET TABLE

    st.subheader("Dataset Table")

    st.dataframe(filtered_df.head(row),use_container_width=True)

    # SHOW FULL DATASET
    if st.checkbox("Show Full Dataset"):
        st.dataframe(filtered_df,use_container_width=True)
    st.divider()

    # COLUMNS STATICS

    st.subheader("Columns Statistics")
    numeric_cols = df.select_dtypes(include=["int64","float64"]).columns

    if len(numeric_cols)>0:
        selected_col = st.selectbox("Select Numeric Columns",numeric_cols)
        st.write(filtered_df[selected_col].describe())
    st.divider()

    st.subheader("Download Data")

    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button("Download Filtered Dataset",csv,"filtered_dataset.csv","text/csv")

if selected == "Overview":
    st.title("Uber Operation")
    st.markdown("---")

    # STRATEGIC KPI LAYER

    total_ride = len(df)

    completed_ride = df[df["Booking Status"]=="Completed"]

    total_revenue = completed_ride["Booking Value"].sum()

    avg_distance = completed_ride["Ride Distance"].mean()

    success_rate = (len(completed_ride)/total_ride)*100 if total_ride > 0 else 0

    avg_rating = completed_ride["Customer Rating"].dropna().mean()

    kpi1 , kpi2 , kpi3 , kpi4 = st.columns(4)

    kpi1.metric("Gross Booking Values",f"{total_revenue:,.0f}",
                "Target: 1000000")

    kpi2.metric("Fulfilment Rate",f"{success_rate:.1f}%",
                "-2.4% from previous month","red")

    kpi3.metric("Avg Trip Distance",f"{avg_distance:.2f}km")

    kpi4.metric("Avg Customer Rating",f"{avg_rating:.1f}/5.0")
    st.divider()

    # BUSINESS UNIT PERFORMANCE

    st.subheader("Business Unit Performance")

    bu_metrics = df.groupby("Vehicle Type").agg(
        Total_Booking=("Booking ID","count"),
        Revenue_generated = ("Booking Value","sum"),
        Avg_Distance = ("Ride Distance","mean"),
        Avg_Rating = ("Customer Rating","mean")
    )
    bu_metrics["Revenue Share %"] = (bu_metrics["Revenue_generated"]/total_revenue*100 if total_revenue > 0 else 0)

    st.dataframe(
        bu_metrics.style.format({"Revenue_generated":"{:.2f}",
                                "Avg_Distance":"{:.2f}km",
                                "Avg_Rating":"{:.1f}",
                                "Revenue Share %":"{:.1f}%"}
    ).background_gradient(subset=["Revenue_generated","Total_Booking"],cmap="YlGn"),use_container_width=True)

    st.divider()

    # OPERATIONAL EFFICIENCY

    col_eff , col_can = st.columns(2)
    with col_eff:
        st.subheader("Operational Efficiency")

        eff_df = df.groupby("Vehicle Type")[["Avg VTAT","Avg CTAT"]].mean()

        st.write("Average Turnaround Time(Minutes)")
        st.dataframe(
            eff_df.style.highlight_max(axis=0,color="#ffccff").highlight_min(axis=0,color="#55b9db "),
            use_container_width=True
        )

        # CANCELLATION AUDIT

    with col_can:
            st.subheader("Cancellation Audit")
            status_count = df["Booking Status"].value_counts().to_frame(name="Count")

            status_count["Share %"] = (status_count["Count"]/total_ride*100)
            st.write("Total Rides over View")
            st.dataframe(status_count,use_container_width=True)

    st.divider()

        # FINANCIAL DEEP DIVE

    st.subheader("Financial Deep Dive")

    pay_col , reason_col = st.columns([4,6])

        # PAYMENT ANALYSIS

    with pay_col:
            st.markdown("** Payment Preference **")

            pay_summary = (completed_ride["Payment Method"].value_counts (normalize=True)*100)
            st.dataframe(pay_summary.rename("Usage %"),use_container_width=True)

        # CANCELLATION REASON ANALYSIS

    with reason_col:
            st.markdown("** Primary Cancellation Trigger **")
            cust_reasons = (df["Reason for cancelling by Customer"].dropna().value_counts().head(3))

            drv_reasons = (df["Driver Cancellation Reason"].dropna().value_counts().head(3))

            cust_reasons.index="Customer" + cust_reasons.index
            drv_reasons.index="Driver" + drv_reasons.index

            reason_df = pd.concat([cust_reasons,drv_reasons]).to_frame()
            st.dataframe(reason_df)

            # DATA QUALITY AUDIT

    with st.expander("Data Quality & Audit Logs"):
                audit1 , audit2 = st.columns(2)
                audit1.write(f"Duplicate Records :**{df.duplicated().sum()}")
                audit2.write(f"Missing Booking Values : **{df["Booking Value"].isna().sum()}")
                st.info("Missing Bookings Value are expected for cancelled or no driver rides")
                st.success("Executive Overview Generated from Operational Dataset")

if selected == "Ride Analytics":

    st.title("Advance Ride Intelligence Dashboard")
    st.divider()

    completed = df[df["Booking Status"]=="Completed"]

    # SUNBURN CHART

    st.subheader("Revenue Hierarchy")

    fig1 = px.sunburst(completed,path=["Vehicle Type","Payment Method"],
                       values="Booking Value",
                        color="Booking Value",
                       color_continuous_scale="Turbo")

    fig1.update_layout(height=500)

    st.plotly_chart(fig1,use_container_width=True)
    st.divider()

    st.subheader("Revenue Distribution")
    fig2 = px.treemap(completed,path=["Vehicle Type","Payment Method"],
                      values="Booking Value",
                      color="Booking Value",
                      color_continuous_scale="Blues")

    fig2.update_layout(margin = dict(t=20,l=20,r=0,b=0),height=420)
    st.plotly_chart(fig2,use_container_width=True)

    st.subheader("Customer Rating Spread")

    fig3 = px.box(completed,x="Vehicle Type",y="Customer Rating",color="Vehicle Type")
    fig3.update_layout(showlegend=False,height=420)
    st.plotly_chart(fig3,use_container_width=True)


    # SANKEY DIAGRAM

    st.subheader("Ride Flow Analysis")
    flow = df.groupby(["Vehicle Type","Booking Status"]).size().reset_index(name="count")
    source_label = flow["Vehicle Type"].unique().tolist()
    target_labels = flow["Booking Status"].unique().tolist()

    labels = source_label + target_labels

    source = flow["Vehicle Type"].apply(
        lambda x : labels.index(x)).tolist()
    target = flow["Booking Status"].apply(
        lambda x: labels.index(x)).tolist()
    value= flow["count"].tolist()

    import plotly.graph_objects as go

    fig4 = go.Figure(data=[go.Sankey(
        node=dict(
            pad=15,
            thickness=20,
            line=dict(color="blue",width=0.5),label=labels
        ),
        link=dict(source=source,
                  target=target,
                  value=value)
    )])
    fig4.update_layout(height=500)
    st.plotly_chart(fig4,use_container_width=True)

if selected == "Data Assistant":
    st.title("Data Assistant")
    st.divider()

    st.write("Ask Questions about the dataset and get visual analytics")
    user_question = st.text_input("Ask Your Question")

    if user_question:
        q = user_question.lower()

        completed = df[df["Booking Status"]=="Completed"]

        #total rides
        if "total rides" in q:
            total = len(df)
            st.success(f"Total Rides in dataset: {total}")

            status = df["Booking Status"].value_counts()

            fig = px.bar(x=status.index,y=status.values,
                     labels={"x":"Booking status","y":"Ride Count"},
                     title="Ride Distribution by status")
            st.plotly_chart(fig,use_container_width=True)

        #revenue analysis
        elif "revenue" in q:
            revenue = completed.groupby("Vehicle Type")["Booking Value"].sum()
            st.success(f"Total Revenue : {revenue.sum():,.2f}")

            fig = px.bar(x=revenue.index,y=revenue.values,
                         title="Revenue by Vehicle type",
                         labels={"x":"Vehicle type","y":"Revenue"})
            st.plotly_chart(fig,use_container_width=True)

        elif "vehicle" in q:
            vehicle = df["Vehicle Type"].value_counts()
            st.success(f"Most Used Vehicle type:{vehicle.idxmax()}")

            fig = px.pie(names=vehicle.index,values=vehicle.values,
                         title="Vehicle usage distribution")
            st.plotly_chart(fig,use_container_width=True)

        #payment analysis

        elif "payment" in q:
            payment = completed["Payment Method"].value_counts()

            fig = px.pie(
                names = payment.index,
                values= payment.values,
                title="Payment method "
            )
            st.plotly_chart(fig,use_container_width=True)

        #cancellation analysis

        elif "cancel" in q:
            cancel = df["Booking Status"].value_counts()
            fig = px.bar(x=cancel.index,y=cancel.values,title="Ride Status",
                         labels={"x":"Booking Status","y":"Ride Count"})

            st.plotly_chart(fig,use_container_width=True)

        elif "rating" in q:
            fig = px.histogram(completed,x="Customer Rating",nbins=10,title="Customer Rating")
            st.plotly_chart(fig,use_container_width=True)
            st.success(f"Average Rating {completed["Customer Rating"].mean():.2f}")

        #Distance analysis

        elif "distance" in q:
            fig = px.scatter(completed,x="Ride Distance",y="Booking Value",color="Vehicle Type",
                             title="Ride Distance vs Booking Value")

            st.plotly_chart(fig,use_container_width=True)
            st.success(f"Average Distance:{completed["Ride Distance"].mean():.2f}")

        else:
            st.warning("Question not recognized. Try asking about cancellations,revenue,vehicle type,distance,payment etc" )
            st.divider()

if selected=="Dashboard":
        st.title("Dashboard")
        col1,col2 = st.columns(2)
        with col1:
            vehicle_count = df["Vehicle Type"].value_counts().reset_index(name="Total Bookings")

            fig = px.bar(vehicle_count,x="Vehicle Type",y="Total Bookings",
                         color="Vehicle Type",title="Total Bookings by Vehicle Type")
            st.plotly_chart(fig,use_container_width=True)

        with col2:
            vehicle_count = df["Vehicle Type"].value_counts().reset_index(name="Booking Value")
            fig1 = px.bar(vehicle_count, x="Vehicle Type", y="Booking Value",
                         color="Vehicle Type",orientation="h", title="Revenue by Vehicle Type")
            st.plotly_chart(fig1, use_container_width=True)
        st.divider()

        col3,col4 = st.columns(2)
        with col3:
            status = df["Booking Status"].value_counts()
            fig = px.pie(names=status.index,values=status.values,hole=0.5)
            st.plotly_chart(fig,use_container_width=True)

        with col4:
            payment = df["Payment Method"].value_counts()
            fig2 = px.pie(names=payment.index, values=payment.values)
            st.plotly_chart(fig2, use_container_width=True)
        st.divider()

        col5,col6 = st.columns(2)
        with col5:
            completed = df[df["Booking Status"]=="Completed"]
            fig = px.scatter(completed, x="Ride Distance", y="Booking Value", color="Vehicle Type",
                             title="Ride Distance vs Booking Value")

            st.plotly_chart(fig, use_container_width=True)

        with col6:
            completed = df[df["Booking Status"] == "Completed"]
            fig1 = px.histogram(completed, x="Customer Rating", nbins=10, title="Customer Rating")
            st.plotly_chart(fig1, use_container_width=True)
        st.divider()

        col7, col8 = st.columns(2)
        with col7:
            cancellation_count = df["Reason for cancelling by Customer"].value_counts().reset_index(name="Count")
            fig = px.bar(cancellation_count, x="Reason for cancelling by Customer", y="Count",
                         color="Reason for cancelling by Customer",
                         title="Cancellation Reasons Analysis")
            st.plotly_chart(fig, use_container_width=True)

        with col8:
            avg_distance = df.groupby("Vehicle Type")["Ride Distance"].mean().reset_index()
            fig1 = px.bar(avg_distance, x="Vehicle Type", y="Ride Distance", color="Vehicle Type",
                         title="Average Distance by Vehicle Type")
            st.plotly_chart(fig1, use_container_width=True)

        col9, col10 = st.columns(2)
        with col9:
            fig = px.histogram(df, x="Booking Value", nbins=10, title="Booking Value Distribution",
                               labels={"Booking Value": "Booking Value", "count": "Frequency"})
            st.plotly_chart(fig, use_container_width=True)

        with col10:
            fig1 = px.scatter(df, x="Avg CTAT", y="Avg VTAT", color="Vehicle Type",
                             title="Operational Efficiency (CTAT vs VTAT)")
            st.plotly_chart(fig1, use_container_width=True)
