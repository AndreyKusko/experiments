

with open("/opt/ass.xlsx", "wb") as binary_file:
    binary_file.write(file)


l = 0
for i in [["7",".",".",".","4",".",".",".","."],[".",".",".","8","6","5",".",".","."],[".","1",".","2",".",".",".",".","."],[".",".",".",".",".","9",".",".","."],[".",".",".",".","5",".","5",".","."],[".",".",".",".",".",".",".",".","."],[".",".",".",".",".",".","2",".","."],[".",".",".",".",".",".",".",".","."],[".",".",".",".",".",".",".",".","."]]:
    l+=1
    if l == 4 or l == 7:
        print(' ')
    print(i[0:3],i[3:6],i[6:])



def for_zip_export__remember_zip_as_bytes__and__remove_archive(main_folder_path):
    """
    Запомнить зип в опертивку в виде байтов и удалить его из папки

    Запомненные байты будут посланы в обжстор
    """
    zip_file_path = f"{main_folder_path}.zip"
    buf = io.BytesIO()
    with open(zip_file_path, "rb") as file_data:
        buf.write(file_data.read())
    buf.seek(0)
    # os.remove(zip_file_path)
    return buf




@staticmethod
def get_file_content_from_obj_store(file_id):
    # todo revert
    with open("/Users/andreycheutin/Desktop/import_reservations__via_geo_point_and_project_scheme_with_time__with_user_phone1.xlsx", "rb") as file:
        return file.read()

    url = MEDIA_STORE_GET_OBJ_LINK.format(file_id)
    response = requests.get(url=url, headers={"X-Meta-Fetch": "1"})
    return response.content
