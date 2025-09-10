#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
from descope import DescopeClient, AuthException
from flask import session, redirect, url_for, request, jsonify
from functools import wraps

# Initialize Descope client
descope_client = None

def setup_descope():
    """Initialize Descope client with project credentials"""
    global descope_client
    project_id = os.getenv("DESCOPE_PROJECT_ID")
    management_key = os.getenv("DESCOPE_MANAGEMENT_KEY")
    
    if not project_id:
        raise ValueError("DESCOPE_PROJECT_ID environment variable is required")
    
    try:
        descope_client = DescopeClient(project_id=project_id, management_key=management_key)
        print("Descope client initialized successfully")
        return True
    except Exception as e:
        print("Failed to initialize Descope client: " + str(e))
        return False

def verify_session_token(session_token):
    """Verify a Descope session token and return user info"""
    if not descope_client:
        if not setup_descope():
            return None
    
    try:
        # Verify the session token
        jwt_response = descope_client.validate_session(session_token=session_token)
        if jwt_response and jwt_response.get("sub"):
            return {
                "user_id": jwt_response["sub"],
                "email": jwt_response.get("email", ""),
                "name": jwt_response.get("name", "")
            }
    except AuthException as e:
        print("Session verification failed: " + str(e))
    
    return None

def get_user_interests(user_id):
    """Get user interests from Descope user data"""
    if not descope_client:
        if not setup_descope():
            return []
    
    try:
        # Get user details from Descope
        user = descope_client.management.user.load(user_id)
        if user and user.get("customAttributes"):
            custom_attrs = user.get("customAttributes", {})
            return custom_attrs.get("interests", [])
    except Exception as e:
        print("Failed to get user interests: " + str(e))
    
    return []

def save_user_interests(user_id, interests, location=None):
    """Save user interests to Descope user data"""
    if not descope_client:
        if not setup_descope():
            return False
    
    try:
        # Prepare custom attributes
        custom_attributes = {"interests": interests}
        if location:
            custom_attributes["location"] = location
        
        # Update user in Descope
        descope_client.management.user.update(
            user_id=user_id,
            custom_attributes=custom_attributes
        )
        return True
    except Exception as e:
        print("Failed to save user interests: " + str(e))
        return False

def login_required(f):
    """Decorator to require authentication for routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({"error": "Authentication required"}), 401
        return f(*args, **kwargs)
    return decorated_function