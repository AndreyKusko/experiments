from ma_saas.utils.encriptor import (
    encrypt_objstore_obj_id,
    encrypt_public_link_obj_id,
    decrypt_value_public_link_obj_id,
    decrypt_value_public_objstore_link_id,
)


def test__encrypt_objstore_obj_id__value():
    value = "01EHWF33Y33QMNMGFZAM5GGYEJ"
    encrypted_value = encrypt_objstore_obj_id(value)
    decrypted_value = decrypt_value_public_objstore_link_id(encrypted_value)
    assert value == decrypted_value


def test__encrypt_public_link_obj_id__value():
    value = "01EHWF33Y33QMNMGFZAM5GGYEJ"
    encrypted_value = encrypt_public_link_obj_id(value)
    decrypted_value = decrypt_value_public_link_obj_id(encrypted_value)
    assert value == decrypted_value
