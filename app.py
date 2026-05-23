from flask import Flask, render_template, request, redirect, session
import pandas as pd
import mysql.connector
from mlxtend.preprocessing import TransactionEncoder
from mlxtend.frequent_patterns import apriori, association_rules

app = Flask(__name__)

app.secret_key = 'foodai123'

# =========================
# DATABASE MYSQL
# =========================

mydb = mysql.connector.connect(
    host='localhost',
    user='root',
    password='',
    database='foodai'
)

cursor = mydb.cursor(
    dictionary=True,
    buffered=True
)
# =========================
# MEMBACA DATASET
# =========================

df = pd.read_csv('Indonesian_Food_Recipes.csv')

recipes = df['Ingredients Cleaned'].dropna().head(1000)

transactions = []

for item in recipes:

    ingredients = item.split(',')

    ingredients = [x.strip().lower() for x in ingredients]

    transactions.append(ingredients)

# =========================
# APRIORI
# =========================

te = TransactionEncoder()

te_array = te.fit(transactions).transform(transactions)

encoded = pd.DataFrame(te_array, columns=te.columns_)

frequent_itemsets = apriori(
    encoded,
    min_support=0.01,
    use_colnames=True
)

rules = association_rules(
    frequent_itemsets,
    metric='confidence',
    min_threshold=0.2
)
# =========================
# HOME
# =========================

@app.route('/', methods=['GET', 'POST'])

def index():

    recommendations = []

    if request.method == 'POST':

        ingredient = request.form['ingredient'].lower()
        search_query = ingredient

        # simpan history
        if 'username' in session:

            sql = "INSERT INTO history (username, ingredient) VALUES (%s,%s)"

            val = (session['username'], ingredient)

            cursor.execute(sql, val)

            mydb.commit()

        # cari resep berdasarkan bahan
        for index, row in df.iterrows():

            ingredients = str(row['Ingredients Cleaned']).lower()

            if ingredient in ingredients:

                recommendations.append({

                    'id': index,

                    'title': row['Title'],

                    'ingredients': row['Ingredients Cleaned'],

                    'steps': row['Steps']

                })

    return render_template(
    'index.html',
    recommendations=recommendations,
    username=session.get('username'),
    search_query=search_query if request.method == 'POST' else ''
)
# =========================
# REGISTER
# =========================

@app.route('/register', methods=['GET', 'POST'])
def register():

    if request.method == 'POST':

        username = request.form['username']
        email = request.form['email']
        password = request.form['password']

        sql = "INSERT INTO users (username,email,password) VALUES (%s,%s,%s)"

        val = (username, email, password)

        cursor.execute(sql, val)

        mydb.commit()

        return redirect('/login')

    return render_template('register.html')

# =========================
# LOGIN
# =========================

@app.route('/login', methods=['GET', 'POST'])
def login():

    error = ''

    if request.method == 'POST':

        username = request.form['username']
        password = request.form['password']

        sql = "SELECT * FROM users WHERE username=%s AND password=%s"

        val = (username, password)

        cursor.execute(sql, val)

        user = cursor.fetchone()

        if user:

            session['username'] = user['username']

            return redirect('/')

        else:

            error = 'Username atau password salah'

    return render_template('login.html', error=error)
# =========================
# LOGOUT
# =========================

@app.route('/logout')
def logout():

    session.pop('username', None)

    return redirect('/')

# =========================
# PROFILE
# =========================

@app.route('/profile')

def profile():

    if 'username' not in session:

        return redirect('/login')

    username = session['username']

    # ambil user
    sql = "SELECT * FROM users WHERE username=%s"

    val = (username,)

    cursor.execute(sql, val)

    user = cursor.fetchone()

    # ambil history
    sql2 = """
    SELECT * FROM history
    WHERE username=%s
    ORDER BY id DESC
    """

    cursor.execute(sql2, val)

    histories = cursor.fetchall()

    return render_template(

        'profile.html',

        username=username,

        histories=histories,

        user=user

    )

# =========================
# EDIT PROFILE
# =========================

@app.route('/edit_profile', methods=['GET', 'POST'])

def edit_profile():

    if 'username' not in session:

        return redirect('/login')

    username = session['username']

    if request.method == 'POST':

        new_username = request.form['username']

        bio = request.form['bio']

        avatar = request.form['avatar']

        sql = """
        UPDATE users
        SET username=%s, bio=%s, avatar=%s
        WHERE username=%s
        """

        val = (
            new_username,
            bio,
            avatar,
            username
        )

        cursor.execute(sql, val)

        mydb.commit()

        session['username'] = new_username

        return redirect('/profile')

    sql = "SELECT * FROM users WHERE username=%s"

    val = (username,)

    cursor.execute(sql, val)

    user = cursor.fetchone()

    return render_template(
        'edit_profile.html',
        user=user
    )

# =========================
# CHATBOT
# =========================

@app.route('/chatbot', methods=['GET', 'POST'])

def chatbot():

    user_message = ''
    response = ''

    if request.method == 'POST':

        user_message = request.form['message'].lower()

        # =========================
        # RESPON AI
        # =========================

        if 'ayam' in user_message:

            response = '''
🍗 Dari bahan ayam kamu bisa mencoba:

• Ayam goreng crispy
• Soto ayam
• Ayam bakar kecap
• Ayam sambal pedas

Tips:
Tambahkan bawang putih dan kecap agar lebih gurih 😋
'''

        elif 'telur' in user_message:

            response = '''
🍳 Ide masakan telur:

• Telur dadar
• Telur balado
• Nasi goreng telur
• Omelette keju

Tips:
Campur daun bawang agar aroma lebih enak 👌
'''

        elif 'mie' in user_message:

            response = '''
🍜 Menu mie yang bisa dibuat:

• Mie goreng
• Mie nyemek
• Mie kuah pedas
• Indomie carbonara

Tips:
Tambahkan cabai dan telur biar makin mantap 🔥
'''

        elif 'nasi' in user_message:

            response = '''
🍚 Rekomendasi menu nasi:

• Nasi goreng
• Nasi ayam crispy
• Nasi telur
• Nasi kebuli sederhana
'''

        elif 'pedas' in user_message:

            response = '''
🌶️ Pecinta pedas wajib coba:

• Seblak
• Ayam geprek
• Mie pedas level
• Oseng mercon
'''

        elif 'halo' in user_message or 'hai' in user_message:

            response = '''
Halo juga 👋

Aku adalah FoodAI Assistant 🤖
Aku bisa membantu rekomendasi resep makanan berdasarkan bahan yang kamu punya 🍜
'''

        elif 'terima kasih' in user_message:

            response = '''
Sama-sama 😄

Semoga masakannya enak yaa 🍜
'''

        else:

            response = f'''
🤖 Maaf, aku belum mengenali:

"{user_message}"

Coba gunakan kata seperti:
• ayam
• telur
• mie
• nasi
• pedas
'''

    return render_template(

        'chatbot.html',

        response=response,

        user_message=user_message

    )

# =========================
# DETAIL
# =========================

@app.route('/detail/<int:id>')

def detail(id):

    row = df.iloc[id]

    recipe = {

        'title': row['Title'],

        'ingredients': row['Ingredients Cleaned'],

        'steps': row['Steps']

    }

    return render_template(
        'detail.html',
        recipe=recipe
    )
# =========================
# RUN
# =========================

if __name__ == '__main__':

    app.run(debug=True)