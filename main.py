#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Community Volunteer Matcher MCP Server with Descope Authentication
"""

import os
from dotenv import load_dotenv
from mcp.server import Server
from mcp.server.stdio import stdio_server
import asyncio
import json

# Load environment variables
load_dotenv()

# Import auth functions
from auth_setup import setup_descope, verify_session_token, get_user_interests, save_user_interests

# Define interest categories
class InterestCategory:
    ANIMALS = "animals"
    ENVIRONMENT = "environment"
    EDUCATION = "education"
    HEALTHCARE = "healthcare"
    HOMELESSNESS = "homelessness"
    ARTS_CULTURE = "arts_culture"
    COMMUNITY = "community"
    TECHNOLOGY = "technology"
    SENIORS = "seniors"
    YOUTH = "youth"

# Sample volunteer opportunities
SAMPLE_OPPORTUNITIES = [
    {
        "id": "1",
        "title": "Beach Cleanup Day",
        "organization": "Ocean Preservation Society",
        "description": "Help clean up local beaches and protect marine life",
        "categories": ["environment"],
        "location": "Santa Monica Beach, CA",
        "date": "2023-10-15",
        "time": "9:00 AM - 12:00 PM",
        "registration_link": "https://example.com/beach-cleanup"
    },
    {
        "id": "2",
        "title": "Animal Shelter Helper",
        "organization": "Paws and Claws Rescue",
        "description": "Walk dogs and socialize cats at our shelter",
        "categories": ["animals"],
        "location": "Los Angeles, CA",
        "date": "2023-10-20",
        "time": "1:00 PM - 4:00 PM",
        "registration_link": "https://example.com/animal-shelter"
    }
]

class VolunteerMatcherServer:
    def __init__(self):
        self.server = Server("community-volunteer-matcher")
        self.setup_handlers()
        self.user_data = {}  # Temporary storage for demo
    
    def setup_handlers(self):
        @self.server.list_tools()
        async def list_tools():
            return [
                {
                    "name": "find_volunteer_opportunities",
                    "description": "Find volunteer opportunities based on interests and location",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "interests": {
                                "type": "array",
                                "items": {"type": "string", "enum": ["animals", "environment", "education", "healthcare", "homelessness", "arts_culture", "community", "technology", "seniors", "youth"]},
                                "description": "List of interests to match against"
                            },
                            "location": {
                                "type": "string",
                                "description": "Location to search for opportunities (optional)"
                            },
                            "max_results": {
                                "type": "number",
                                "description": "Maximum number of results to return (default: 5)"
                            }
                        },
                        "required": ["interests"]
                    }
                },
                {
                    "name": "set_user_interests",
                    "description": "Set or update user interests for volunteer matching",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "interests": {
                                "type": "array",
                                "items": {"type": "string", "enum": ["animals", "environment", "education", "healthcare", "homelessness", "arts_culture", "community", "technology", "seniors", "youth"]},
                                "description": "List of user interests"
                            },
                            "location": {
                                "type": "string",
                                "description": "User's location (optional)"
                            }
                        },
                        "required": ["interests"]
                    }
                },
                {
                    "name": "get_user_interests",
                    "description": "Get current user interests for volunteer matching",
                    "inputSchema": {
                        "type": "object",
                        "properties": {}
                    }
                }
            ]
        
        @self.server.call_tool()
        async def call_tool(name, arguments):
            if name == "find_volunteer_opportunities":
                return await self.find_volunteer_opportunities(arguments)
            elif name == "set_user_interests":
                return await self.set_user_interests(arguments)
            elif name == "get_user_interests":
                return await self.get_user_interests(arguments)
            else:
                raise ValueError("Unknown tool: " + name)
    
    async def find_volunteer_opportunities(self, arguments):
        try:
            interests = arguments.get("interests", [])
            location = arguments.get("location", "").lower()
            max_results = arguments.get("max_results", 5)
            
            matched_opportunities = []
            for opp in SAMPLE_OPPORTUNITIES:
                interest_match = any(category in interests for category in opp["categories"])
                location_match = True
                if location and location not in opp["location"].lower():
                    location_match = False
                
                if interest_match and location_match:
                    matched_opportunities.append(opp)
                    if len(matched_opportunities) >= max_results:
                        break
            
            if not matched_opportunities:
                return [{"type": "text", "text": "No volunteer opportunities found matching your criteria."}]
            
            result_text = "Found " + str(len(matched_opportunities)) + " volunteer opportunities:\n\n"
            for i, opp in enumerate(matched_opportunities, 1):
                result_text += str(i) + ". **" + opp["title"] + "** - " + opp["organization"] + "\n"
                result_text += "   Location: " + opp["location"] + "\n"
                result_text += "   Description: " + opp["description"] + "\n"
                result_text += "   Categories: " + ", ".join(opp["categories"]) + "\n"
                result_text += "   Register: " + opp["registration_link"] + "\n\n"
            
            return [{"type": "text", "text": result_text}]
            
        except Exception as e:
            return [{"type": "text", "text": "Error finding opportunities: " + str(e)}]
    
    async def set_user_interests(self, arguments):
        try:
            session_token = arguments.get("session_token")
            if not session_token:
                return [{"type": "text", "text": "Authentication required. Please provide a session token."}]
            
            # Verify user session
            user_info = verify_session_token(session_token)
            if not user_info:
                return [{"type": "text", "text": "Invalid session token. Please login again."}]
            
            interests = arguments.get("interests", [])
            location = arguments.get("location")
            
            # Save to Descope
            success = save_user_interests(user_info["user_id"], interests, location)
            
            if success:
                location_text = " in " + location if location else ""
                return [{"type": "text", "text": "Success! Your interests have been saved: " + ", ".join(interests) + location_text}]
            else:
                return [{"type": "text", "text": "Failed to save your interests. Please try again."}]
                
        except Exception as e:
            return [{"type": "text", "text": "Error saving interests: " + str(e)}]
    
    async def get_user_interests(self, arguments):
        try:
            session_token = arguments.get("session_token")
            if not session_token:
                return [{"type": "text", "text": "Authentication required. Please provide a session token."}]
            
            # Verify user session
            user_info = verify_session_token(session_token)
            if not user_info:
                return [{"type": "text", "text": "Invalid session token. Please login again."}]
            
            # Get from Descope
            interests = get_user_interests(user_info["user_id"])
            
            if not interests:
                return [{"type": "text", "text": "You haven't set any interests yet. Use set_user_interests to tell us what causes you care about."}]
            
            return [{"type": "text", "text": "Your current interests: " + ", ".join(interests)}]
                
        except Exception as e:
            return [{"type": "text", "text": "Error retrieving interests: " + str(e)}]

async def main():
    # Setup Descope
    setup_descope()
    
    # Create server instance
    server = VolunteerMatcherServer()
    
    # Start the server
    async with stdio_server() as (read_stream, write_stream):
        await server.server.run(
            read_stream,
            write_stream,
            {
                "name": "community-volunteer-matcher",
                "version": "1.0.0"
            }
        )

if __name__ == "__main__":
    print("Starting Community Volunteer Matcher MCP Server with Authentication...")
    asyncio.run(main())
    