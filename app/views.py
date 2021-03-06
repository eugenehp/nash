# Copyright 2014 SolidBuilds.com. All rights reserved
#
# Authors: Ling Thio <ling.thio@gmail.com>


from flask import redirect, render_template, render_template_string, Blueprint
from flask import request, url_for, jsonify
from flask_user import current_user, login_required, roles_accepted
import json, random
import cPickle as pickle

from app.init_app import app, db
from app.models import UserProfileForm, FriendForm, Graph, User, Friendship

# The Home page is accessible to anyone
@app.route('/')
def home_page():
    return render_template('pages/home_page.html')

@app.route('/graphs')
@login_required  # Limits access to authenticated users
def graph_list_page():
    graphs = []
    for g in current_user.graphs_owned:
        graphs.append(g)
    for g in current_user.graphs_helping:
        graphs.append(g)

    return render_template('pages/graph_list_page.html', graphs=graphs)

@app.route('/graph/<id>')
@login_required  # Limits access to authenticated users
def graph_page(id):
    graph = Graph.query.get(id)

    if current_user not in graph.owners and current_user not in graph.helpers:
        return redirect(url_for('graph_list_page'))
    
    nodes = pickle.loads(str(graph.nodes))
    edges = pickle.loads(str(graph.edges))
    return render_template('pages/graph_page.html', save_id=id,
                           nodes=json.dumps(nodes), edges=json.dumps(edges))
        
@app.route('/newgraph')
@login_required  # Limits access to authenticated users
def graph_create_page():
    print 'newgraph'
    return render_template('pages/graph_page.html',
                           nodes=json.dumps([]),
                           edges=json.dumps([]))

@app.route('/_save_graph', methods=['POST'])
@login_required  # Limits access to authenticated users
def save_graph():
    data = json.loads(request.data)
    save_id = data['save_id']
    save_name = data['save_name']
    if not save_name:
        save_name = "NO NAME"
    nodes = data['nodes']
    edges = data['edges']
    graph = Graph.query.get(save_id)
    if graph is None:
        graph = Graph()
    graph.name = save_name
    graph.nodes = pickle.dumps(nodes)
    graph.edges = pickle.dumps(edges)
    graph.owners = [current_user]
    
    # Save graph
    db.session.commit()

    print pickle.loads(str(graph.nodes))

    return jsonify(result="success")

@app.route('/_share_graph', methods=['POST'])
@login_required  # Limits access to authenticated users
def share_graph():
    data = json.loads(request.data)
    graph_id = data['graph_id']
    user_id = data['user_id']
    graph = Graph.query.get(graph_id)
    user = User.query.get(user_id)
    graph.helpers.append(user)

    db.session.commit()

    return jsonify(result="success")


# The Admin page is accessible to users with the 'admin' role
@app.route('/admin')
@roles_accepted('admin')  # Limits access to users with the 'admin' role
def admin_page():
    return render_template('pages/admin_page.html')


@app.route('/friends', methods=['GET', 'POST'])
@login_required
def friends_page():
    form = FriendForm(request.form)

    if request.method == 'POST' and form.validate():
        user = User()
        form.populate_obj(user)
        users = list(User.query.filter(User.email==user.email).all())
        print users
        print [user.email for user in users]
        assert len(users) <= 1
        if len(users) == 1:
            friendship = Friendship()
            friendship.friender = current_user
            friendship.friendee = users[0]
            current_user.friendships.append(friendship)

        print current_user.friendships
            
        db.session.commit()
            
    return render_template('pages/friends_page.html',
                           friendships=current_user.friendships, form=form)

@app.route('/pages/profile', methods=['GET', 'POST'])
@login_required
def user_profile_page():
    # Initialize form
    form = UserProfileForm(request.form, current_user)

    # Process valid POST
    if request.method == 'POST' and form.validate():
        # Copy form fields to user_profile fields
        form.populate_obj(current_user)

        # Save user_profile
        db.session.commit()

        # Redirect to home page
        return redirect(url_for('home_page'))

    # Process GET or invalid POST
    return render_template('pages/user_profile_page.html',
                           form=form)


