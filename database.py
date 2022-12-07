import sqlite3
 
class Database:

  def __init__(self, database_file):
    self.connection = sqlite3.connect(database_file)
    self.cursor = self.connection.cursor()
  
  def user_exists(self, user_id):
    with self.connection:
      result = self.cursor.execute("SELECT * FROM `users` WHERE `id` = ?", (user_id,)).fetchall()
      return bool(len(result))

  def add_user(self, user_id):
    with self.connection:
      self.cursor.execute("INSERT INTO `users` (`id`) VALUES (?)", (user_id,))
      self.connection.commit()

  def add_photo(self, user_id, image_name):
    with self.connection:
      self.cursor.execute("INSERT INTO `images` (`user_id`, `id`) VALUES (?,?)", (user_id, image_name))
      self.connection.commit()

  def user_photo_exists(self, user_id, image_name):
    with self.connection:
      result = self.cursor.execute("SELECT * FROM `images` WHERE (`user_id`, `id`) = (?,?)", (user_id, image_name)).fetchall()
      return bool(len(result))

  def user_photos(self, user_id):
    with self.connection:
      result = self.cursor.execute("SELECT id FROM `images` WHERE `user_id` = ?", (user_id,)).fetchall()
      return result

  def clear_user_photos(self, user_id):
    with self.connection:
      self.cursor.execute("DELETE FROM `images` WHERE `user_id` = ?", (user_id,))

  def close(self):
    self.connection.close()