from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import random
import secrets
from datetime import datetime

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)  # For session management

# Game state storage
class GameState:
    def __init__(self):
        self.players = {}  # {player_name: {"role": role, "joined_at": datetime}}
        self.game_started = False
        self.roles_assigned = False
        
    def reset_game(self):
        self.players = {}
        self.game_started = False
        self.roles_assigned = False
    
    def add_player(self, player_name):
        if player_name not in self.players and not self.game_started:
            self.players[player_name] = {
                "role": None,
                "joined_at": datetime.now()
            }
            return True
        return False
    
    def get_player_count(self):
        return len(self.players)
    
    def assign_roles(self):
        if self.roles_assigned:
            return False
            
        num_players = len(self.players)
        if num_players < 5:
            return False
        
        # Determine role distribution
        if num_players <= 6:
            wolves = 1
            doctors = 1
        elif 7 <= num_players <= 12:
            wolves = 2
            doctors = 2
        else:
            return False
        
        villagers = num_players - wolves - doctors
        
        # Create role list
        roles = ['Wolf'] * wolves + ['Doctor'] * doctors + ['Villager'] * villagers
        random.shuffle(roles)
        
        # Assign roles to players
        player_names = list(self.players.keys())
        for i, player_name in enumerate(player_names):
            self.players[player_name]["role"] = roles[i]
        
        self.roles_assigned = True
        self.game_started = True
        return True

# Global game state
game_state = GameState()

@app.route('/')
def index():
    return render_template('index.html', 
                         player_count=game_state.get_player_count(),
                         game_started=game_state.game_started)

@app.route('/join', methods=['GET', 'POST'])
def join_game():
    if request.method == 'POST':
        player_name = request.form['player_name'].strip()
        
        if not player_name:
            flash('Please enter a valid name!', 'error')
            return render_template('join.html')
        
        if game_state.game_started:
            flash('Game has already started!', 'error')
            return render_template('join.html')
        
        if game_state.add_player(player_name):
            session['player_name'] = player_name
            flash(f'Welcome {player_name}! Waiting for other players...', 'success')
            return redirect(url_for('waiting_room'))
        else:
            flash('Name already taken or game in progress!', 'error')
    
    return render_template('join.html')

@app.route('/waiting')
def waiting_room():
    if 'player_name' not in session:
        return redirect(url_for('join_game'))
    
    return render_template('waiting.html', 
                         player_name=session['player_name'],
                         players=list(game_state.players.keys()),
                         player_count=game_state.get_player_count(),
                         game_started=game_state.game_started)

@app.route('/start_game', methods=['POST'])
def start_game():
    if game_state.get_player_count() < 5:
        return jsonify({'success': False, 'message': 'Need at least 5 players!'})
    
    if game_state.get_player_count() > 12:
        return jsonify({'success': False, 'message': 'Maximum 12 players allowed!'})
    
    if game_state.assign_roles():
        return jsonify({'success': True, 'message': 'Game started! Roles assigned!'})
    else:
        return jsonify({'success': False, 'message': 'Failed to start game!'})

@app.route('/role')
def view_role():
    if 'player_name' not in session:
        return redirect(url_for('join_game'))
    
    player_name = session['player_name']
    
    if not game_state.game_started:
        return redirect(url_for('waiting_room'))
    
    if player_name not in game_state.players:
        flash('Player not found!', 'error')
        return redirect(url_for('join_game'))
    
    role = game_state.players[player_name]['role']
    
    # Role descriptions
    role_descriptions = {
        'Wolf': 'You are a Wolf! Your goal is to eliminate villagers without being caught.',
        'Doctor': 'You are a Doctor! You can save players from the wolves.',
        'Villager': 'You are a Villager! Work with others to identify and eliminate the wolves.'
    }
    
    return render_template('role.html', 
                         player_name=player_name,
                         role=role,
                         description=role_descriptions.get(role, ''))

@app.route('/admin/reset', methods=['POST'])
def reset_game():
    game_state.reset_game()
    session.clear()
    return jsonify({'success': True, 'message': 'Game reset!'})

@app.route('/status')
def game_status():
    return jsonify({
        'player_count': game_state.get_player_count(),
        'game_started': game_state.game_started,
        'players': list(game_state.players.keys())
    })

# HTML Templates as strings (in a real app, these would be separate files)
@app.route('/templates')
def get_templates():
    return "Templates should be in separate files"

if __name__ == '__main__':
    # Create templates directory structure
    import os
    
    # Create templates directory if it doesn't exist
    if not os.path.exists('templates'):
        os.makedirs('templates')
    
    # Create HTML templates
    templates = {
        'templates/base.html': '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}Mafia Game{% endblock %}</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 0; padding: 20px; background: #f0f0f0; }
        .container { max-width: 600px; margin: 0 auto; background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        h1, h2 { color: #333; text-align: center; }
        .btn { background: #007bff; color: white; padding: 10px 20px; border: none; border-radius: 5px; cursor: pointer; font-size: 16px; }
        .btn:hover { background: #0056b3; }
        .btn-danger { background: #dc3545; }
        .btn-danger:hover { background: #c82333; }
        .btn-success { background: #28a745; }
        .btn-success:hover { background: #218838; }
        .form-group { margin: 15px 0; }
        .form-control { width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 5px; font-size: 16px; }
        .alert { padding: 10px; margin: 10px 0; border-radius: 5px; }
        .alert-success { background: #d4edda; color: #155724; border: 1px solid #c3e6cb; }
        .alert-error { background: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }
        .player-list { background: #f8f9fa; padding: 15px; border-radius: 5px; margin: 10px 0; }
        .player-count { font-weight: bold; color: #007bff; }
        .role-card { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 10px; text-align: center; margin: 20px 0; }
        .role-wolf { background: linear-gradient(135deg, #ff6b6b 0%, #ee5a24 100%); }
        .role-doctor { background: linear-gradient(135deg, #00d2d3 0%, #54a0ff 100%); }
        .role-villager { background: linear-gradient(135deg, #5f27cd 0%, #00d2d3 100%); }
    </style>
</head>
<body>
    <div class="container">
        {% with messages = get_flashed_messages(with_categories=true) %}
            {% if messages %}
                {% for category, message in messages %}
                    <div class="alert alert-{{ 'error' if category == 'error' else 'success' }}">
                        {{ message }}
                    </div>
                {% endfor %}
            {% endif %}
        {% endwith %}
        
        {% block content %}{% endblock %}
    </div>
</body>
</html>
        ''',
        
        'templates/index.html': '''
{% extends "base.html" %}

{% block title %}Mafia Game - Home{% endblock %}

{% block content %}
<h1>🐺 Mafia Role Assignment Game</h1>

<div class="player-list">
    <h3>Current Status</h3>
    <p><span class="player-count">{{ player_count }}</span> players connected</p>
    {% if game_started %}
        <p><strong>Game Status:</strong> <span style="color: green;">In Progress</span></p>
    {% else %}
        <p><strong>Game Status:</strong> <span style="color: orange;">Waiting for Players</span></p>
    {% endif %}
</div>

<div style="text-align: center; margin: 20px 0;">
    {% if not game_started %}
        <a href="{{ url_for('join_game') }}" class="btn btn-success">Join Game</a>
    {% else %}
        <a href="{{ url_for('view_role') }}" class="btn">View My Role</a>
    {% endif %}
</div>

<h3>Game Rules</h3>
<ul>
    <li><strong>6 or fewer players:</strong> 1 Wolf, 1 Doctor, rest Villagers</li>
    <li><strong>7-12 players:</strong> 2 Wolves, 2 Doctors, rest Villagers</li>
    <li><strong>Minimum:</strong> 5 players required</li>
</ul>

<h3>Roles</h3>
<ul>
    <li><strong>🐺 Wolf:</strong> Eliminate villagers without being caught</li>
    <li><strong>👨‍⚕️ Doctor:</strong> Save players from the wolves</li>
    <li><strong>👥 Villager:</strong> Identify and eliminate the wolves</li>
</ul>
{% endblock %}
        ''',
        
        'templates/join.html': '''
{% extends "base.html" %}

{% block title %}Join Game{% endblock %}

{% block content %}
<h2>Join the Game</h2>

<form method="POST">
    <div class="form-group">
        <label for="player_name">Enter your name:</label>
        <input type="text" id="player_name" name="player_name" class="form-control" 
               placeholder="Your name" required maxlength="20">
    </div>
    <div style="text-align: center;">
        <button type="submit" class="btn btn-success">Join Game</button>
        <a href="{{ url_for('index') }}" class="btn">Back to Home</a>
    </div>
</form>
{% endblock %}
        ''',
        
        'templates/waiting.html': '''
{% extends "base.html" %}

{% block title %}Waiting Room{% endblock %}

{% block content %}
<h2>Waiting Room</h2>

<p>Welcome, <strong>{{ player_name }}</strong>!</p>

<div class="player-list">
    <h3>Players in Game ({{ player_count }}/12)</h3>
    <ul>
    {% for player in players %}
        <li>{{ player }} {% if player == player_name %}<em>(You)</em>{% endif %}</li>
    {% endfor %}
    </ul>
</div>

{% if not game_started %}
    <div style="text-align: center; margin: 20px 0;">
        {% if player_count >= 5 %}
            <button onclick="startGame()" class="btn btn-success">Start Game</button>
        {% else %}
            <p><em>Need at least 5 players to start (currently {{ player_count }})</em></p>
        {% endif %}
    </div>
{% else %}
    <div style="text-align: center; margin: 20px 0;">
        <a href="{{ url_for('view_role') }}" class="btn">View My Role</a>
    </div>
{% endif %}

<script>
function startGame() {
    fetch('/start_game', { method: 'POST' })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert('Game started! Roles have been assigned!');
            window.location.href = '/role';
        } else {
            alert(data.message);
        }
    });
}

// Auto-refresh page every 3 seconds to see new players
setInterval(() => {
    if (!{{ game_started|tojson }}) {
        location.reload();
    }
}, 3000);
</script>
{% endblock %}
        ''',
        
        'templates/role.html': '''
{% extends "base.html" %}

{% block title %}Your Role{% endblock %}

{% block content %}
<h2>Your Secret Role</h2>

<div class="role-card role-{{ role.lower() }}">
    <h1>{{ role }}</h1>
    <p>{{ description }}</p>
</div>

<div style="text-align: center; margin: 20px 0;">
    <a href="{{ url_for('index') }}" class="btn">Back to Home</a>
    <button onclick="resetGame()" class="btn btn-danger">Reset Game (Admin)</button>
</div>

<script>
function resetGame() {
    if (confirm('Are you sure you want to reset the game? This will clear all players and roles.')) {
        fetch('/admin/reset', { method: 'POST' })
        .then(response => response.json())
        .then(data => {
            alert('Game reset!');
            window.location.href = '/';
        });
    }
}
</script>

<style>
.role-card h1 { margin: 0; font-size: 2.5em; }
</style>
{% endblock %}
        '''
    }
    
    # Write template files
    for filename, content in templates.items():
        with open(filename, 'w') as f:
            f.write(content.strip())
    
    print("Mafia Game Web App Starting...")
    print("Players can connect at: http://YOUR_IP:8000")
    print("Replace YOUR_IP with your actual IP address")
    print("\nTo find your IP address:")
    print("- Windows: ipconfig")
    print("- Mac/Linux: ifconfig or ip addr")
    
    # Run the app
    app.run(host='0.0.0.0', port=8000, debug=True)
