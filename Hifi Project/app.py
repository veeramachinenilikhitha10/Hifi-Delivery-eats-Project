from flask import Flask, render_template, request, jsonify, send_file
import sqlite3
import os
from fpdf import FPDF

app = Flask(__name__)
UPLOAD_FOLDER = 'static/uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


def get_db_connection():
    conn = sqlite3.connect('enhanced_menu_management.db')
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/admin')
def admin():
    return render_template('adminpanel.html')

@app.route('/api/menu_items', methods=['GET', 'POST'])
def menu_items():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if request.method == 'GET':
        # Fetch menu items
        try:
            cursor.execute('''
                SELECT 
                    mi.MenuItemID, 
                    mi.Name, 
                    mi.Description, 
                    mi.Price, 
                    mi.ImageURL, 
                    mi.AvailabilityStatus,
                    c.CategoryName,
                    c.CategoryID,
                    GROUP_CONCAT(dp.PreferenceName, ', ') as DietaryPreferences
                FROM MenuItems mi
                LEFT JOIN Category c ON mi.CategoryID = c.CategoryID
                LEFT JOIN MenuItemDietaryPreferences midp ON mi.MenuItemID = midp.MenuItemID
                LEFT JOIN DietaryPreferences dp ON midp.PreferenceID = dp.PreferenceID
                GROUP BY mi.MenuItemID
            ''')
            menu_items = cursor.fetchall()
            return jsonify([dict(item) for item in menu_items])
        except Exception as e:
            return jsonify({"error": str(e)}), 500
        finally:
            conn.close()

    elif request.method == 'POST':
        # Add new menu item
        data = request.json
        try:
            cursor.execute('''
                INSERT INTO MenuItems 
                (Name, Description, Price, CategoryID, AvailabilityStatus, ImageURL) 
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                data['Name'], 
                data['Description'], 
                float(data['Price']), 
                int(data['CategoryID']), 
                data.get('AvailabilityStatus', 1),
                data.get('ImageURL', '')
            ))
            menu_item_id = cursor.lastrowid

            if 'DietaryPreferences' in data and data['DietaryPreferences']:
                cursor.executemany('''
                    INSERT INTO MenuItemDietaryPreferences (MenuItemID, PreferenceID) 
                    VALUES (?, ?)
                ''', [(menu_item_id, pref_id) for pref_id in data['DietaryPreferences']])

            conn.commit()
            return jsonify({"message": "Menu item added successfully", "id": menu_item_id}), 201
        except Exception as e:
            conn.rollback()
            return jsonify({"error": str(e)}), 400
        finally:
            conn.close()

# Update existing menu item
@app.route('/api/menu_items', methods=['PUT'])
def update_menu_item():
    try:
        data = request.json
        menu_item_id = data.get('MenuItemID')

        if not menu_item_id:
            return jsonify({"error": "MenuItemID is required"}), 400

        # Database connection
        conn = get_db_connection()
        cursor = conn.cursor()

        # Update query
        cursor.execute('''
            UPDATE MenuItems
            SET Name = ?, Description = ?, Price = ?, CategoryID = ?, ImageURL = ?, AvailabilityStatus = ?, ModifiedDate = CURRENT_TIMESTAMP
            WHERE MenuItemID = ?
        ''', (
            data.get('Name'),
            data.get('Description'),
            data.get('Price'),
            data.get('CategoryID'),
            data.get('ImageURL'),
            data.get('AvailabilityStatus'),
            menu_item_id
        ))

        conn.commit()
        conn.close()

        if cursor.rowcount == 0:
            return jsonify({"error": "No menu item found with the given ID"}), 404

        return jsonify({"message": "Menu item updated successfully"}), 200

    except Exception as e:
        # Log the error for debugging
        print(f"Error: {e}")
        return jsonify({"error": "An internal error occurred"}), 500

# Delete menu item
@app.route('/api/menu_items/<int:item_id>', methods=['DELETE'])
def modify_menu_item(item_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    if request.method == 'DELETE':
        # Delete menu item
        try:
            cursor.execute('DELETE FROM MenuItemDietaryPreferences WHERE MenuItemID=?', (item_id,))
            cursor.execute('DELETE FROM MenuItems WHERE MenuItemID=?', (item_id,))
            conn.commit()
            return jsonify({"message": "Menu item deleted successfully"}), 200
        except Exception as e:
            conn.rollback()
            return jsonify({"error": str(e)}), 400
        finally:
            conn.close()

@app.route('/api/categories', methods=['GET'])
def get_categories():
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('SELECT * FROM Category')
        categories = cursor.fetchall()
        return jsonify([dict(category) for category in categories])
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()

@app.route('/api/dietary_preferences', methods=['GET'])
def get_dietary_preferences():
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('SELECT * FROM DietaryPreferences')
        preferences = cursor.fetchall()
        return jsonify([dict(preference) for preference in preferences])
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()

#Export pdf
@app.route('/api/export_menu_items', methods=['GET'])
def export_menu_items():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            SELECT 
                mi.Name, 
                mi.Description, 
                mi.Price, 
                mi.ImageURL,
                c.CategoryName
            FROM MenuItems mi
            LEFT JOIN Category c ON mi.CategoryID = c.CategoryID
        ''')
        menu_items = cursor.fetchall()

        # Create PDF
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)

        pdf.cell(200, 10, txt="Menu Items", ln=True, align='C')
        pdf.ln(10)

        for item in menu_items:
            pdf.set_font("Arial", 'B', size=12)
            pdf.cell(0, 10, f"Name: {item['Name']}", 0, 1)
            pdf.set_font("Arial", size=12)
            pdf.cell(0, 10, f"Description: {item['Description']}", 0, 1)
            pdf.cell(0, 10, f"Price: ${item['Price']:.2f}", 0, 1)
            pdf.cell(0, 10, f"Category: {item['CategoryName']}", 0, 1)
            
            """Add Image
            image_path = item['ImageURL']
            if image_path:
                # Construct the absolute path to the image
                absolute_image_path = os.path.join(app.config['UPLOAD_FOLDER'], image_path.lstrip('/'))
                print(f"Checking image path: {absolute_image_path}")  # Debugging line
                if os.path.exists(absolute_image_path):
                    pdf.cell(0, 10, 'Image:', 0, 1)
                    pdf.image(absolute_image_path, x=10, y=None, w=50, h=30)  # Adjust image size and position as needed
                else:
                    pdf.cell(0, 10, 'Image: N/A', 0, 1)
                    print(f"Image not found: {absolute_image_path}")  # Log missing or invalid images
            else:
                pdf.cell(0, 10, 'Image: N/A', 0, 1)
            """

            pdf.ln(5)

        # Save PDF to a temporary file
        pdf_file_path = 'static/uploads/menu_items.pdf'
        pdf.output(pdf_file_path)

        return send_file(pdf_file_path, as_attachment=True)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()


if __name__ == '__main__':
    app.run(debug=True)
