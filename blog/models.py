from py2neo import Graph, Node, Relationship
from passlib.hash import bcrypt
from datetime import datetime
import os
import uuid

url = os.environ.get('GRAPHENEDB_URL', 'http://localhost:7474')
username = os.environ.get('NEO4J_USERNAME')
password = os.environ.get('NEO4J_PASSWORD')

graph = Graph(url + '/db/data/', username=username, password=password)

class User:
    def __init__(self, username):
        self.username = username

    def find(self):
        user = graph.find_one('User', 'username', self.username)
        return user

    def register(self, password):
        if not self.find():
            user = Node('User', username=self.username, password=bcrypt.encrypt(password))
            graph.create(user)
            return True
        else:
            return False

    def verify_password(self, password):
        user = self.find()
        if user:
            return bcrypt.verify(password, user['password'])
        else:
            return False

    def add_post(self, title, tags, text):
        user = self.find()
        post = Node(
            'Post',
            id=str(uuid.uuid4()),
            title=title,
            text=text,
            timestamp=timestamp(),
            date=date()
        )
        rel = Relationship(user, 'PUBLISHED', post)
        graph.create(rel)

        tags = [x.strip() for x in tags.lower().split(',')]
        for name in set(tags):
            tag = Node('Tag', name=name)
            graph.merge(tag)

            rel = Relationship(tag, 'TAGGED', post)
            graph.create(rel)

    def add_reply( self , post_id , text):
        user = self.find()
        reply = Node(
            'reply',
            id=str(uuid.uuid4()),
            text=text,
	    to=post_id, 
            timestamp=timestamp(),
            date=date()
        )
        post = graph.find_one('Post', 'id', post_id)
        rel = Relationship(user, 'REPLIED', reply)
	graph.create(rel)
	rel = Relationship(reply, 'REPLIEDto', post)
        graph.create(rel)


    def like_post(self, post_id,reply_id):
        user = self.find()
        post = graph.find_one('reply', 'id', reply_id)
        graph.merge(Relationship(user, 'LIKED', post))

    def get_recent_posts(self):
        query = '''
        MATCH (user:User)-[:PUBLISHED]->(post:Post)<-[:TAGGED]-(tag:Tag)
        WHERE user.username = {username}
        RETURN post, COLLECT(tag.name) AS tags
        ORDER BY post.timestamp DESC LIMIT 5
        '''

        return graph.run(query, username=self.username)

    def get_similar_users(self):
        # Find three users who are most similar to the logged-in user
        # based on tags they've both blogged about.
        query = '''
        MATCH (you:User)-[:PUBLISHED]->(:Post)<-[:TAGGED]-(tag:Tag),
              (they:User)-[:PUBLISHED]->(:Post)<-[:TAGGED]-(tag)
        WHERE you.username = {username} AND you <> they
        WITH they, COLLECT(DISTINCT tag.name) AS tags
        ORDER BY SIZE(tags) DESC LIMIT 3
        RETURN they.username AS similar_user, tags
        '''

        return graph.run(query, username=self.username)

    def get_commonality_of_user(self, other):
        # Find how many of the logged-in user's posts the other user
        # has liked and which tags they've both blogged about.
        query = '''
        MATCH (they:User {username: {they} })
        MATCH (you:User {username: {you} })
        OPTIONAL MATCH (they)-[:PUBLISHED]->(:Post)<-[:TAGGED]-(tag:Tag),
                       (you)-[:PUBLISHED]->(:Post)<-[:TAGGED]-(tag)
        RETURN SIZE((they)-[:LIKED]->(:Post)<-[:PUBLISHED]-(you)) AS likes,
               COLLECT(DISTINCT tag.name) AS tags
        '''

        return graph.run(query, they=other.username, you=self.username).next

    def search_posts(self,searchtag):
        query = '''MATCH (user:User)-[:PUBLISHED]->(post:Post)<-[:TAGGED]-(tag:Tag) where tag.name="'''+searchtag.lower()+'''" 
        RETURN post , user.username AS username ,COLLECT(tag.name) AS tags '''

        return graph.run(query)
    
    def show_post(self,post_id):
	query = '''MATCH (user:User)-[:PUBLISHED]->(post:Post)<-[:TAGGED]-(tag:Tag) where post.id="'''+post_id+'''"  
        RETURN post , user.username AS username 
        	,COLLECT(tag.name) AS tags
        '''

        return graph.run(query)

    def show_ans(self,post_id):
	query = '''
	MATCH (ruser:User)-[:REPLIED]->(reply:reply) where reply.to="'''+post_id+'''"

	OPTIONAL MATCH (user:User)-[liked:LIKED]->(reply1:reply) where reply1.id=reply.id 
        RETURN reply,ruser.username AS replyuser ,COUNT(user) AS likecount
        ORDER BY reply.timestamp LIMIT 10
        '''

        return graph.run(query)


    def show_answers(self,post_id):
	query = '''MATCH (user:User)-[:PUBLISHED]->(post:Post)<-[:TAGGED]-(tag:Tag) where post.id="'''+post_id+'''" 
        OPTIONAL MATCH (ruser:User)-[:REPLIED]->(reply:reply) where reply.to=post.id 
        RETURN post , reply,ruser.username AS replyuser , user.username AS username '''

        return graph.run(query)

    def get_like(self , reply_id):
	query = '''  MATCH (ruser:User)-[liked:LIKED]->(reply:reply) where reply.id="'''+reply_id+'''" 
	RETURN  COUNT(ruser)'''
	return graph.run(query)





def get_todays_recent_posts():
    query = '''
    MATCH (user:User)-[:PUBLISHED]->(post:Post)<-[:TAGGED]-(tag:Tag)
    RETURN user.username AS username, post, COLLECT(tag.name) AS tags
    ORDER BY post.timestamp DESC LIMIT 10
    '''

    return graph.run(query)

def timestamp():
    epoch = datetime.utcfromtimestamp(0)
    now = datetime.now()
    delta = now - epoch
    return delta.total_seconds()

def date():
    return datetime.now().strftime('%Y-%m-%d')
