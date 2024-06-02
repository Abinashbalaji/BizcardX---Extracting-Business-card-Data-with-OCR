

from PIL import Image
import easyocr
import numpy as np
import pandas as pd
import re
import streamlit as st
import io
import sqlite3

def img_to_text(i_path):
    input_img = Image.open(i_path)
    image_arr= np.array(input_img)
    reader= easyocr.Reader(['en'])
    text = reader.readtext(image_arr, detail=0)

    return text,input_img

def extracted_text(texts):
  extracted_dic = {"NAME":[],"DESIGNATION":[],"COMPANY_NAME":[],"PHONE":[],"WEBSITE":[],"EMAIL":[],"ADDRESS":[],"PINCODE":[]}

  extracted_dic["NAME"].append(texts[0])
  extracted_dic["DESIGNATION"].append(texts[1])

  for i in range(2,len(texts)):
    if texts[i].startswith("+") or (texts[i].replace("-","").isdigit() and "-" in texts[i]):
      extracted_dic["PHONE"].append(texts[i])

    elif "WWW" in texts[i] or "www" in texts[i] or "Www" in texts[i] or "wWw" in texts[i] or "wwW" in texts[i]:
      extracted_dic["WEBSITE"].append(texts[i])

    elif "@" in texts[i] and ".com" in texts[i]:
      extracted_dic["EMAIL"].append(texts[i])

    elif "TamilNadu" in texts[i] or "Tamilnadu" in texts[i] or "tamilnadu" in texts[i] or texts[i].isdigit():
      extracted_dic["PINCODE"].append(texts[i])

    elif re.match(r'^[A-Za-z]',texts[i]):
      extracted_dic["COMPANY_NAME"].append(texts[i])

    else:
      remove_marks = re.sub(r'[,;]','', texts[i])
      extracted_dic["ADDRESS"].append(texts[i])

  for key,value in extracted_dic.items():
    if len(value)>0:
      concatenate = ' '.join(value)
      extracted_dic[key] = [concatenate]
    else:
        value = 'NA'
        extracted_dic[key] = [value]

  return extracted_dic


st.set_page_config(layout= "wide")
st.title(":rainbow[BizCardX EXTRACTING BUSINESS CARD DATA WITH OCR]")
st.write("")

Menu = st.sidebar.radio("Select",["Home","Upload & Modify","Delete"])

if Menu == "Home":
  st.header(":grey[USED SKILLS:]")
  st.write("⦿ OCR (Optical Character Recognition)")
  st.write("⦿ SQLite3 ")
  st.write("⦿ Streamlit")
  st.write("⦿ Data Extraction")

  st.header(':grey[PROJECT SUMMARY:]')

  st.subheader('Required packages:')
  st.write("""You will need to install Python, Streamlit,
          easyOCR, and a database management system like SQLite or MySQL.""")
  st.subheader('User Interface:')
  st.write("""A simple and intuitive user interface using
          Streamlit that guides users through the process of uploading the business
          card image and extracting its information. You can use widgets like file
          uploader, buttons, and text boxes to make the interface more interactive.""")
  st.subheader('Image processing and OCR:')
  st.write("""easyOCR is used to extract the
          relevant information from the uploaded business card image.
          Image processing techniques like resizing, cropping, and thresholding to
          enhance the image quality before passing it to the OCR engine.""")
  st.subheader('Extracted information:')
  st.write("""Once the information has been extracted,
          display it in a clean and organized manner in the Streamlit GUI.
          widgets like tables, text boxes, and labels to present the information.""")
  st.subheader('Database integration:')
  st.write("""SQLite3 was used to save the extracted Details""")


elif Menu=="Upload & Modify":
  Img = st.file_uploader("Upload the Image", type=["png","jpeg","jpg"])

  if Img is not None:
    st.image(Img, width=300)

    text,input_img = img_to_text(Img)
    text_dic = extracted_text(text)

    if text_dic:
       st.success("Text Extracted Successfully")

    df = pd.DataFrame(text_dic)

    # Covert Image to Bytes
    Img_bytes = io.BytesIO()
    input_img.save(Img_bytes, format = "PNG")

    img_data = Img_bytes.getvalue()

    # Create a Dictionary
    data = {"image":[img_data]}
    df_1 = pd.DataFrame(data)

    df_concat = pd.concat([df,df_1],axis=1)#axis 1 is used to concatenate by coulmn wise

    st.dataframe(df_concat)

    button_1 = st.button("SAVE",use_container_width = True)

    if button_1:

      mydb=sqlite3.connect("bizcardx.db")
      cursor = mydb.cursor()

      # Table Creating

      Create_table_query = '''CREATE TABLE IF NOT EXISTS bizcard_details(name VARCHAR(200),
                                                                        designation VARCHAR(200),
                                                                        company_name VARCHAR(200),
                                                                        phone VARCHAR(200),
                                                                        website text,
                                                                        email VARCHAR(200),
                                                                        address text,
                                                                        pincode text(200),
                                                                        image text)'''

      cursor.execute(Create_table_query)
      mydb.commit()

      # Insert Query

      insert_query = '''INSERT INTO bizcard_details(name, designation, company_name, phone, website, email, address, pincode, image)

                        VALUES(?,?,?,?,?,?,?,?,?)'''

      datas = df_concat.values.tolist()[0]
      cursor.execute(insert_query,datas)
      mydb.commit()

      st.success("Saved Successfully")

  Method = st.radio("Select",["None","Preview","Modify"])

  if Method=="None":
    st.write("")

  if Method == "Preview":
    mydb=sqlite3.connect("bizcardx.db")
    cursor = mydb.cursor()

    # select query
    select_query = "SELECT * FROM bizcard_details"

    cursor.execute(select_query)
    table = cursor.fetchall()
    mydb.commit()

    table_df = pd.DataFrame(table,columns =("NAME","DESIGNATION", "COMPANY_NAME", "PHONE", "WEBSITE","EMAIL", "ADDRESS","PINCODE","IMAGE"))

    st.dataframe(table_df)

  if Method=="Modify":
    mydb=sqlite3.connect("bizcardx.db")
    cursor = mydb.cursor()

    # select query
    select_query = "SELECT * FROM bizcard_details"

    cursor.execute(select_query)
    table = cursor.fetchall()
    mydb.commit()

    table_df = pd.DataFrame(table,columns =("NAME","DESIGNATION", "COMPANY_NAME", "PHONE", "WEBSITE","EMAIL", "ADDRESS","PINCODE","IMAGE"))

    col1,col2 = st.columns(2)
    with col1:
      selected_name = st.selectbox("Select the Name", table_df["NAME"])

    df_3 = table_df[table_df["NAME"] == selected_name]
    st.dataframe(df_3)

    df_4 = df_3.copy()

    col1,col2 = st.columns(2)
    with col1:
      modify_name = st.text_input("Name",df_3["NAME"].unique()[0])
      modify_desig = st.text_input("Designation",df_3["DESIGNATION"].unique()[0])
      modify_company = st.text_input("Company Name",df_3["COMPANY_NAME"].unique()[0])
      modify_phone = st.text_input("Phone",df_3["PHONE"].unique()[0])
      modify_image = st.text_input("Image",df_3["IMAGE"].unique()[0])

      df_4["NAME"] = modify_name
      df_4["DESIGNATION"] = modify_desig
      df_4["COMPANY_NAME"] = modify_company
      df_4["PHONE"] = modify_phone
      df_4["IMAGE"] = modify_image


    with col2:
      modify_website = st.text_input("Website",df_3["WEBSITE"].unique()[0])
      modify_email = st.text_input("E Mail",df_3["EMAIL"].unique()[0])
      modify_address = st.text_input("Address",df_3["ADDRESS"].unique()[0])
      modify_pincode = st.text_input("Pincode",df_3["PINCODE"].unique()[0])

      df_4["WEBSITE"] = modify_website
      df_4["EMAIL"] = modify_email
      df_4["ADDRESS"] = modify_address
      df_4["PINCODE"] = modify_pincode

    st.dataframe(df_4)

    col1,col2 = st.columns(2)
    with col1:
      button_3 = st.button("Modify",use_container_width = True)

    if button_3:
      mydb=sqlite3.connect("bizcardx.db")
      cursor = mydb.cursor()

      cursor.execute(f"DELETE FROM bizcard_details WHERE NAME ='{selected_name}'")
      mydb.commit()

      # Insert Query

      insert_query = '''INSERT INTO bizcard_details(name, designation, company_name, phone, website, email, address, pincode, image)

                        VALUES(?,?,?,?,?,?,?,?,?)'''

      datas = df_4.values.tolist()[0]
      cursor.execute(insert_query,datas)
      mydb.commit()

      st.success("Modified Successfully")



elif Menu=="Delete":

  mydb=sqlite3.connect("bizcardx.db")
  cursor = mydb.cursor()

  col1, col2 = st.columns(2)
  with col1:

    cursor.execute("SELECT NAME FROM bizcard_details")
    table1 = cursor.fetchall()
    mydb.commit()

    names = []

    for i in table1:
      names.append(i[0])

    name_select = st.selectbox("Select the Name", names)

  with col2:

    select_query = f"SELECT DESIGNATION FROM bizcard_details WHERE NAME = '{name_select}'"

    cursor.execute(select_query)
    table2 = cursor.fetchall()
    mydb.commit()

    designation = []

    for j in table2:
      designation.append(j[0])

    designation_select = st.selectbox("Select the Designation", designation)

  if name_select and designation_select:
    col1, col2 = st.columns(2)

    with col1:
      st.write(f"Selected Name: {name_select}")
      st.write((""))
      st.write(f"Selected Designation: {designation_select}")

      remove = st.button("Delete", use_container_width = True)

      if remove:
        cursor.execute(f"DELETE FROM bizcard_details WHERE NAME ='{name_select}' AND DESIGNATION = '{designation_select}' ")
        mydb.commit()

        st.warning("Deleted")

