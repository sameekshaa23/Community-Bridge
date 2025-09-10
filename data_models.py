from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum

# Types of volunteer opportunities users can choose from
class InterestCategory(str, Enum):
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

# What we need to know about a user's interests
class UserInterests(BaseModel):
    user_id: str = Field(..., description="The unique ID for each user")
    interests: List[InterestCategory] = Field(..., description="What causes the user cares about")
    location: Optional[str] = Field(None, description="Where the user wants to volunteer")
    availability: Optional[List[str]] = Field(None, description="When the user is free to help")

# Information about a volunteer opportunity
class VolunteerOpportunity(BaseModel):
    id: str = Field(..., description="Unique ID for this opportunity")
    title: str = Field(..., description="Name of the volunteer opportunity")
    organization: str = Field(..., description="Who's organizing this event")
    description: str = Field(..., description="What volunteers will be doing")
    categories: List[InterestCategory] = Field(..., description="What causes this supports")
    location: str = Field(..., description="Where the volunteering happens")
    date: Optional[str] = Field(None, description="When it takes place")
    time: Optional[str] = Field(None, description="What time it happens")
    registration_link: str = Field(..., description="Link to sign up")
    image_url: Optional[str] = Field(None, description="Picture of the activity")

# What we need to find matching opportunities
class OpportunityMatchRequest(BaseModel):
    interests: List[InterestCategory] = Field(..., description="What the user cares about")
    location: Optional[str] = Field(None, description="Where to look for opportunities")
    max_results: Optional[int] = Field(5, description="How many results to show")

# The opportunities we found for the user
class OpportunityMatchResponse(BaseModel):
    opportunities: List[VolunteerOpportunity] = Field(..., description="Matching volunteer opportunities")
    match_count: int = Field(..., description="How many matches we found")