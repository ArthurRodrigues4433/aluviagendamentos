import sqlite3

conn = sqlite3.connect('aluvi.db')
cursor = conn.cursor()

# Ver estrutura da tabela
cursor.execute('PRAGMA table_info(usuarios)')
columns = cursor.fetchall()
print('Estrutura da tabela usuarios:')
for col in columns:
    print(f'  {col[1]} ({col[2]})')

print()

cursor.execute('SELECT id, nome, email, ativo, mensalidade_pago, data_vencimento_mensalidade, criado_em, criado_por FROM usuarios WHERE admin = 0')
owners = cursor.fetchall()

print('Donos no banco:')
for owner in owners:
    print(f'ID: {owner[0]}, Nome: {owner[1]}, Email: {owner[2]}, Ativo: {owner[3]}, Pago: {owner[4]}, Vencimento: {owner[5]}, Criado: {owner[6]}, Criado_por: {owner[7]}')

conn.close()