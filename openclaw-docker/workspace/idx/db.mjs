// Week 3: MySQL connection module (handbook code, converted to JavaScript).
// Connection details come from the environment (set in docker-compose.yml / .env).
// The login is idx_user, which can only read (SELECT).
import mysql from "mysql2/promise";

const pool = mysql.createPool({
  host:     process.env.MYSQL_HOST,
  user:     process.env.MYSQL_USER,
  password: process.env.MYSQL_PASSWORD,
  database: process.env.MYSQL_DATABASE,
  waitForConnections: true,
  connectionLimit: 10,
  queueLimit: 0,
});

// Runs a parameterized query: values go in `params`, never pasted into the SQL text.
export async function query(sql, params = []) {
  const [rows] = await pool.execute(sql, params);
  return rows;
}

export async function closePool() {
  await pool.end();
}
