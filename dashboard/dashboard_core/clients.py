"""Python script to create and return a boto3 session."""
import boto3
import streamlit as st


@st.cache_resource(show_spinner=False)
def get_boto3_session(region: str) -> boto3.Session:
    """Returns a boto3 session."""
    return boto3.Session(region_name=region)
