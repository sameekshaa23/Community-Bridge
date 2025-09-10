from mcp.server import Server
from mcp.server.models import InitializationOptions
from mcp.types import ListToolsResult, Tool, TextContent
import json
from typing import List
import auth_setup
from data_models import *

# Some example volunteer opportunities to get started
# In a real app, these would come from a database or API
SAMPLE_VOLUNTEER_JOBS = [
    {
        "id": "1",
        "title": "Beach Cleanup Day",
        "organization": "Ocean Preservation Society",
        "description": "Help clean up our local beaches and protect marine life from pollution. Gloves and bags provided!",
        "categories": ["environment"],
        "location": "Santa Monica Beach, CA",
        "date": "2023-10-15",
        "time": "9:00 AM - 12:00 PM",
        "registration_link": "https://example.com/beach-cleanup",
        "image_url": "https://example.com/images/beach-cleanup.jpg"
    },
    {
        "id": "2",
        "title": "Animal Shelter Helper",
        "organization": "Paws and Claws Rescue",
        "description": "Spend time with our furry friends! Walk dogs, socialize cats, and help with cleaning duties.",
        "categories": ["animals"],
        "location": "Los Angeles, CA",
        "date": "2023-10-20",
        "time": "1:00 PM - 4:00 PM",
        "registration_link": "https://example.com/animal-shelter",
        "image_url": "https://example.com/images/animal-shelter.jpg"
    },
    {
        "id": "3",
        "title": "Food Bank Volunteer",
        "organization": "Community Food Share",
        "description": "Help sort and package food donations for families in need. No experience needed!",
        "categories": ["community", "homelessness"],
        "location": "Downtown LA",
        "date": "2023-10-18",
        "time": "10:00 AM - 2:00 PM",
        "registration_link": "https://example.com/food-bank",
        "image_url": "https://example.com/images/food-bank.jpg"
    },
    {
        "id": "4",
        "title": "Tech Tutor for Seniors",
        "organization": "Digital Literacy Foundation",
        "description": "Teach seniors how to use smartphones, computers, and stay safe online. Patience is the only requirement!",
        "categories": ["technology", "seniors"],
        "location": "Westwood Community Center, CA",
        "date": "2023-10-22",
        "time": "3:00 PM - 5:00 PM",
        "registration_link": "https://example.com/tech-tutor",
        "image_url": "https://example.com/images/tech-tutor.jpg"
    },
    {
        "id": "5",
        "title": "Park Restoration Volunteer",
        "organization": "City Parks Department",
        "description": "Help restore native plants and maintain hiking trails in our beautiful local parks.",
        "categories": ["environment", "community"],
        "location": "Griffith Park, CA",
        "date": "2023-10-25",
        "time": "8:00 AM - 12:00 PM",
        "registration_link": "https://example.com/park-restoration",
        "image_url": "https://example.com/images/park-restoration.jpg"
    }
]

class VolunteerMatchmaker:
    def __init__(self):
        self.server = Server("community-volunteer-matchmaker")
        self.setup_tools()
    
    def setup_tools(self):
        @self.server.list_tools()
        async def show_available_tools() -> ListToolsResult:
            """Show what this volunteer matchmaker can do"""
            tools = [
                Tool(
                    name="find_volunteer_opportunities",
                    description="Find volunteer opportunities that match your interests and location",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "interests": {
                                "type": "array",
                                "items": {"type": "string", "enum": [ic.value for ic in InterestCategory]},
                                "description": "What causes are you passionate about?"
                            },
                            "location": {
                                "type": "string",
                                "description": "Where would you like to volunteer? (city or area)"
                            },
                            "max_results": {
                                "type": "number",
                                "description": "How many results would you like to see? (default: 5)"
                            }
                        },
                        "required": ["interests"]
                    }
                ),
                Tool(
                    name="set_my_interests",
                    description="Tell us what causes you care about to get better volunteer recommendations",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "interests": {
                                "type": "array",
                                "items": {"type": "string", "enum": [ic.value for ic in InterestCategory]},
                                "description": "What causes matter to you?"
                            },
                            "location": {
                                "type": "string",
                                "description": "Where are you located? (helps find nearby opportunities)"
                            }
                        },
                        "required": ["interests"]
                    }
                ),
                Tool(
                    name="check_my_interests",
                    description="See what volunteer causes you've told us you care about",
                    inputSchema={
                        "type": "object",
                        "properties": {}
                    }
                )
            ]
            return ListToolsResult(tools=tools)
        
        @self.server.call_tool()
        async def use_tool(name: str, arguments: dict) -> List[TextContent]:
            """Handle requests to use our tools"""
            if name == "find_volunteer_opportunities":
                return await self.find_opportunities(arguments)
            elif name == "set_my_interests":
                return await self.save_interests(arguments)
            elif name == "check_my_interests":
                return await self.show_interests(arguments)
            else:
                raise ValueError(f"We don't have a tool called '{name}'")
    
    async def find_opportunities(self, arguments: dict) -> List[TextContent]:
        """Find volunteer opportunities that match what the user cares about"""
        try:
            # Understand what the user is looking for
            request = OpportunityMatchRequest(**arguments)
            
            # Look for matching opportunities
            good_matches = []
            for opportunity_data in SAMPLE_VOLUNTEER_JOBS:
                opportunity = VolunteerOpportunity(**opportunity_data)
                
                # Check if this matches the user's interests
                matches_interests = any(category in request.interests for category in opportunity.categories)
                
                # Check if it's in the right area if specified
                matches_location = True
                if request.location and request.location.lower() not in opportunity.location.lower():
                    matches_location = False
                
                if matches_interests and matches_location:
                    good_matches.append(opportunity)
                    
                    # Stop if we have enough results
                    if request.max_results and len(good_matches) >= request.max_results:
                        break
            
            # Prepare our response
            response = OpportunityMatchResponse(
                opportunities=good_matches,
                match_count=len(good_matches)
            )
            
            # If we didn't find anything
            if not good_matches:
                return [TextContent(
                    type="text",
                    text="We couldn't find any volunteer opportunities that match your criteria. 😔\n\nTry broadening your interests or checking a different location."
                )]
            
            # Format the results in a friendly way
            result_text = f"🎉 We found {len(good_matches)} volunteer opportunities for you!\n\n"
            
            for i, opportunity in enumerate(good_matches, 1):
                result_text += f"{i}. **{opportunity.title}** with {opportunity.organization}\n"
                result_text += f"   📍 {opportunity.location}\n"
                result_text += f"   📝 {opportunity.description}\n"
                if opportunity.date:
                    result_text += f"   📅 {opportunity.date}"
                    if opportunity.time:
                        result_text += f" at {opportunity.time}"
                    result_text += "\n"
                result_text += f"   🏷️  Causes: {', '.join(opportunity.categories)}\n"
                result_text += f"   🔗 Sign up: {opportunity.registration_link}\n\n"
            
            result_text += "Thank you for wanting to make a difference in your community! 🌟"
            
            return [TextContent(type="text", text=result_text)]
            
        except Exception as e:
            return [TextContent(
                type="text", 
                text=f"Sorry, we encountered a problem while searching: {str(e)}"
            )]
    
    async def save_interests(self, arguments: dict) -> List[TextContent]:
        """Save what causes a user cares about"""
        try:
            # In a real app, we'd get the user ID from their session
            user_id = "current_user"
            
            interests = arguments.get("interests", [])
            location = arguments.get("location")
            
            # Make sure the interests are valid
            valid_interests = []
            for interest in interests:
                if interest in [ic.value for ic in InterestCategory]:
                    valid_interests.append(interest)
            
            # Save the preferences (commented out for this example)
            # success = auth_setup.save_user_preferences(user_id, valid_interests, location)
            success = True
            
            if success:
                location_text = f" in {location}" if location else ""
                return [TextContent(
                    type="text",
                    text=f"✅ Great! We've saved your interests: {', '.join(valid_interests)}{location_text}.\n\nNow you can use 'find_volunteer_opportunities' to discover ways to help!"
                )]
            else:
                return [TextContent(
                    type="text",
                    text="❌ We couldn't save your preferences. Please try again in a moment."
                )]
                
        except Exception as e:
            return [TextContent(
                type="text", 
                text=f"Sorry, we encountered a problem: {str(e)}"
            )]
    
    async def show_interests(self, arguments: dict) -> List[TextContent]:
        """Show a user what causes they've told us they care about"""
        try:
            # In a real app, we'd get the user ID from their session
            user_id = "current_user"
            
            # Get saved interests (commented out for this example)
            # interests = auth_setup.get_user_preferences(user_id)
            interests = ["environment", "animals"]  # Example data
            location = "Toronto, CA"  # Example data
            
            if not interests:
                return [TextContent(
                    type="text",
                    text="You haven't told us what causes you care about yet. 😊\n\nUse 'set_my_interests' to let us know what matters to you, and we'll find perfect volunteer opportunities!"
                )]
            
            location_text = f" in {location}" if location else ""
            return [TextContent(
                type="text",
                text=f"Here's what you've told us you care about: {', '.join(interests)}{location_text}.\n\nUse 'find_volunteer_opportunities' to discover ways to make a difference!"
            )]
                
        except Exception as e:
            return [TextContent(
                type="text", 
                text=f"Sorry, we couldn't retrieve your interests: {str(e)}"
            )]