#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from flask import Flask, render_template_string, request, jsonify
import subprocess
import json
import os

app = Flask(__name__)

# HTML template for the web interface
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Volunteer Matchmaker Tester</title>
    <style>
        body { font-family: Arial, sans-serif; max-width: 900px; margin: 0 auto; padding: 20px; background-color: #f5f5f5; }
        .card { border: 1px solid #ddd; padding: 20px; margin: 15px 0; border-radius: 10px; background: white; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .success { background-color: #e8f5e8; border-color: #4caf50; }
        .error { background-color: #ffebee; border-color: #f44336; }
        button { background-color: #4caf50; color: white; padding: 12px 20px; border: none; border-radius: 6px; cursor: pointer; font-size: 14px; margin: 5px; }
        button:hover { background-color: #45a049; }
        input, select { width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 5px; margin: 8px 0; box-sizing: border-box; }
        pre { white-space: pre-wrap; word-wrap: break-word; background: #f8f8f8; padding: 15px; border-radius: 5px; }
        .loading { color: #666; font-style: italic; }
    </style>
</head>
<body>
    <h1>Volunteer Matchmaker Tester</h1>
    <p>Test your MCP server without Claude.ai</p>
    
    <div class="card">
        <h2>Available Tools</h2>
        <button onclick="listTools()">List Tools</button>
        <div id="toolsResult"></div>
    </div>

    <div class="card">
        <h2>Find Volunteer Opportunities</h2>
        <div>
            <label><strong>Interests:</strong> (comma-separated)</label>
            <input type="text" id="interests" value="environment,animals" placeholder="environment,animals,community">
        </div>
        <div>
            <label><strong>Location:</strong></label>
            <input type="text" id="location" value="Los Angeles" placeholder="Enter location (optional)">
        </div>
        <div>
            <label><strong>Max Results:</strong></label>
            <input type="number" id="max_results" value="3" min="1" max="10">
        </div>
        <button onclick="findOpportunities()">Find Opportunities</button>
        <div id="opportunitiesResult"></div>
    </div>

    <div class="card">
        <h2>Set My Interests</h2>
        <div>
            <label><strong>Interests:</strong> (comma-separated)</label>
            <input type="text" id="setInterests" value="environment,community" placeholder="environment,community">
        </div>
        <div>
            <label><strong>Location:</strong></label>
            <input type="text" id="setLocation" value="New York" placeholder="Enter your location">
        </div>
        <button onclick="setInterests()">Save Interests</button>
        <div id="setInterestsResult"></div>
    </div>

    <div class="card">
        <h2>Check My Interests</h2>
        <button onclick="checkInterests()">Check Saved Interests</button>
        <div id="checkInterestsResult"></div>
    </div>

    <script>
        function showLoading(elementId) {
            document.getElementById(elementId).innerHTML = '<div class="loading">Loading...</div>';
        }

        function listTools() {
            showLoading('toolsResult');
            fetch('/list_tools')
                .then(response => response.json())
                .then(data => {
                    document.getElementById('toolsResult').innerHTML = formatResponse(data);
                })
                .catch(error => {
                    document.getElementById('toolsResult').innerHTML = '<div class="error">Error: ' + error.message + '</div>';
                });
        }

        function findOpportunities() {
            showLoading('opportunitiesResult');
            var interests = document.getElementById('interests').value.split(',').map(function(i) {
                return i.trim();
            });
            var params = {
                interests: interests,
                location: document.getElementById('location').value,
                max_results: parseInt(document.getElementById('max_results').value)
            };
            
            fetch('/find_opportunities', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(params)
            })
            .then(response => response.json())
            .then(data => {
                document.getElementById('opportunitiesResult').innerHTML = formatResponse(data);
            })
            .catch(error => {
                document.getElementById('opportunitiesResult').innerHTML = '<div class="error">Error: ' + error.message + '</div>';
            });
        }

        function setInterests() {
            showLoading('setInterestsResult');
            var interests = document.getElementById('setInterests').value.split(',').map(function(i) {
                return i.trim();
            });
            var params = {
                interests: interests,
                location: document.getElementById('setLocation').value
            };
            
            fetch('/set_interests', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(params)
            })
            .then(response => response.json())
            .then(data => {
                document.getElementById('setInterestsResult').innerHTML = formatResponse(data);
            })
            .catch(error => {
                document.getElementById('setInterestsResult').innerHTML = '<div class="error">Error: ' + error.message + '</div>';
            });
        }

        function checkInterests() {
            showLoading('checkInterestsResult');
            fetch('/check_interests')
                .then(response => response.json())
                .then(data => {
                    document.getElementById('checkInterestsResult').innerHTML = formatResponse(data);
                })
                .catch(error => {
                    document.getElementById('checkInterestsResult').innerHTML = '<div class="error">Error: ' + error.message + '</div>';
                });
        }

        function formatResponse(data) {
            if (data.error) {
                return '<div class="error"><strong>Error:</strong> ' + data.error + '</div>';
            }
            if (data.result) {
                return '<div class="success"><pre>' + data.result + '</pre></div>';
            }
            return '<div class="success"><pre>' + JSON.stringify(data, null, 2) + '</pre></div>';
        }
    </script>
</body>
</html>
"""

def run_mcp_command(command_name, arguments=None):
    """Run MCP command using subprocess (compatible with old Python)"""
    try:
        # Create a simple test script without emojis
        test_script = '''# -*- coding: utf-8 -*-
import json

# Sample volunteer opportunities
opportunities = [
    {
        "title": "Beach Cleanup Day",
        "organization": "Ocean Preservation Society", 
        "description": "Help clean up local beaches and protect marine life",
        "location": "Santa Monica Beach, CA",
        "categories": ["environment"],
        "registration_link": "https://example.com/beach-cleanup"
    },
    {
        "title": "Animal Shelter Helper", 
        "organization": "Paws and Claws Rescue",
        "description": "Walk dogs and socialize cats at our shelter",
        "location": "Los Angeles, CA", 
        "categories": ["animals"],
        "registration_link": "https://example.com/animal-shelter"
    },
    {
        "title": "Food Bank Volunteer",
        "organization": "Community Food Share", 
        "description": "Help sort and package food donations",
        "location": "Downtown LA",
        "categories": ["community", "homelessness"],
        "registration_link": "https://example.com/food-bank"
    }
]

def test_command():
    """Test the MCP command"""
    command_name = ''' + json.dumps(command_name) + '''
    arguments = ''' + json.dumps(arguments) + '''
    
    if command_name == "find_volunteer_opportunities":
        interests = arguments.get('interests', [])
        location = arguments.get('location', '')
        max_results = arguments.get('max_results', 3)
        
        # Filter opportunities
        filtered_opps = []
        for opp in opportunities:
            # Check if any category matches interests
            match = False
            for cat in opp['categories']:
                if cat in interests:
                    match = True
                    break
            
            # Check location if specified
            if match and location:
                if location.lower() not in opp['location'].lower():
                    match = False
            
            if match:
                filtered_opps.append(opp)
                if len(filtered_opps) >= max_results:
                    break
        
        # Build result text (without emojis)
        result_text = "Found " + str(len(filtered_opps)) + " volunteer opportunities:\\n\\n"
        for i, opp in enumerate(filtered_opps, 1):
            result_text += str(i) + ". **" + opp['title'] + "** - " + opp['organization'] + "\\n"
            result_text += "   Location: " + opp['location'] + "\\n"
            result_text += "   Description: " + opp['description'] + "\\n"
            result_text += "   Categories: " + ", ".join(opp['categories']) + "\\n"
            result_text += "   Register: " + opp['registration_link'] + "\\n\\n"
        
        return {"content": [{"type": "text", "text": result_text}]}
    
    elif command_name == "set_user_interests":
        interests = arguments.get('interests', [])
        location = arguments.get('location', '')
        location_text = " in " + location if location else ""
        result_text = "Success! Your interests have been saved: " + ", ".join(interests) + location_text + "."
        return {"content": [{"type": "text", "text": result_text}]}
    
    elif command_name == "get_user_interests":
        return {"content": [{"type": "text", "text": "Your interests: environment, animals. Location: Los Angeles"}]}
    
    elif command_name == "list_tools":
        return {
            "tools": [
                {"name": "find_volunteer_opportunities", "description": "Find volunteer opportunities based on interests"},
                {"name": "set_user_interests", "description": "Set your volunteer interests"},
                {"name": "get_user_interests", "description": "Get your current interests"}
            ]
        }

# Run the test
try:
    result = test_command()
    print(json.dumps(result))
except Exception as e:
    print(json.dumps({"error": str(e)}))
'''
        
        # Write and run the script
        with open('temp_test.py', 'w') as f:
            f.write(test_script)
        
        result = subprocess.run(
            ['python', 'temp_test.py'], 
            capture_output=True, 
            text=True, 
            timeout=10
        )
        
        # Clean up
        if os.path.exists('temp_test.py'):
            os.remove('temp_test.py')
        
        if result.returncode == 0 and result.stdout.strip():
            return json.loads(result.stdout)
        else:
            error_msg = result.stderr if result.stderr else "No output from server"
            return {"error": "Command failed: " + error_msg}
            
    except subprocess.TimeoutExpired:
        return {"error": "Command timed out"}
    except json.JSONDecodeError:
        return {"error": "Invalid response from server"}
    except Exception as e:
        return {"error": "Unexpected error: " + str(e)}

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/list_tools')
def list_tools():
    result = run_mcp_command("list_tools")
    return jsonify(result)

@app.route('/find_opportunities', methods=['POST'])
def find_opportunities():
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400
    
    result = run_mcp_command("find_volunteer_opportunities", data)
    return jsonify(result)

@app.route('/set_interests', methods=['POST'])
def set_interests():
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400
    
    result = run_mcp_command("set_user_interests", data)
    return jsonify(result)

@app.route('/check_interests')
def check_interests():
    result = run_mcp_command("get_user_interests", {})
    return jsonify(result)

if __name__ == '__main__':
    print("Starting Volunteer Matchmaker Web UI")
    print("Access at: http://localhost:8002")
    print("This is a demo interface with simulated MCP responses")
    print("Press Ctrl+C to stop the server")
    app.run(debug=True, host='127.0.0.1', port=8002)