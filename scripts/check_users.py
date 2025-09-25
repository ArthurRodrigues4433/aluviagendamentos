import sqlite3

conn = sqlite3.connect('aluvi.db')
cursor = conn.cursor()

cursor.execute('SELECT id, nome, email, telefone, endereco, descricao, logo, ativo, admin FROM usuarios')
usuarios = cursor.fetchall()

print('Usuários:')
for usuario in usuarios:
    print(f'ID: {usuario[0]}')
    print(f'  Nome: {usuario[1]}')
    print(f'  Email: {usuario[2]}')
    print(f'  Telefone: {usuario[3] if usuario[3] else "NULL"}')
    print(f'  Endereco: {usuario[4] if usuario[4] else "NULL"}')
    print(f'  Descricao: {usuario[5] if usuario[5] else "NULL"}')
    print(f'  Logo: {usuario[6] if usuario[6] else "NULL"}')
    print(f'  Ativo: {usuario[7]}')
    print(f'  Admin: {usuario[8]}')
    print()

conn.close()