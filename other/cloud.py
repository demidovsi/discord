import json
import os

from google.cloud import storage
from google.oauth2 import service_account

import config
import common

t = 'w7LCk8Ouwr3DmcKdccKQwpdWwqbCqcOcw5nCuMKyw5zDjsK1wqbDkcOSw4DDiMOrwpJ5XcKZw6HDrMKzw5PCncKyw4rDlsKdwpdmwqTCg3HCv8Ojw5DDjcKqw6DDksOAw4jDm8KdwoBwwqnCqMKrdMKLZG94w6fCpsKcwrrDi8OXwrTCrsOiw5TDjcKiw5fDh23ClMKXwpJ_wp_CqsKiwrJ6w4rCmsKwwovDm2rCmMKqwqLClsKxwoLCqcOSwot3wqHClMKDwo3Dm8KpwrDCn8Oaw5bDnHvCnmnCsMKKw5zClVVwworChcK_w4HDoMOlwrXCt8OTw4LCtsK_w7DCksKHXcKZwp7Cp3HClmXCkcKbwr59woFkwrrCtcKYwqXCuMODwpljwrnCqMKkwofCpMKdemrDk8Ofw4fCjcKyfcOFwr3DgHZ0wojCq8KxwpHCtsOiw6DCvMKuw5fCqsKEw5HCp8Kywo7CjsK8wrfCu8KFwrx7wpHCocOewqvCmsKrwr3DjsKQwrbCvMKwwpXCssK3wqXCjMKrwrvDhMK4wqTCqsK_w6vClMKawqfCkMKhwqJ1wo_CssKcw5HCusKxwrzDncKfwrDCuMOWwq7DicOqw4PCpcK0w6vCpcOCwqjDoMKqwp7CusK9woDCnHXDkMONwqHCpcOCw4bCnsKIwqDCuMOCwovDj8K-w4fCosOnwrnDhMKKwqvCosOAwq7CqMKGwovCrcOhw4jChcKHw6PDqMKFdcOKw5HCr8Kgw4TDmsK_wovCrMObw7PCu8KewozCucKhw7BjwqjCscKtw5nCg8KAw6HDp8OGwq3CtMKVwprCm8Ovw5LCmcKnw67DnMKzwo_Cm8KqwqfCosOadcKUwqzCmcKxw4TCgMKuw4bCrHbCssOGwq_DksOcw6fCpsKtw4fCtMOWwrLCnMKcwrrCt8OkwqDCgHPDkcOGw4PCpsONw4XCqcK9w6PCl3vDg8KtwrnCmcKgwq3DqMOKd8KaY8Kaw4HCrcKGXsKMwqvCvcK4wqTCpsOpwpbCscK1wrnCtcKrw6vDg8K9wrXDmsK9w6HCvcK0wp_DiMOBw4TCh3XCqcOGw5HCnMK7w6jCtsKpbsOcwrXCnsKNwrrCo8KhwrXCucKnw6Vvwr99wpvCrcOcwprChMKYwr7CvMK6wpLDqcK5wq10wrXClsKZwq_Cv8K7w4PCo8OJwr3Dg8Kpw6JresOPw6fCgmR2w4HCjsKywpLCrsKhwqXCr8Ofw4jCp8OIw6TCtsOCwqHDqsOhw4jClsK2Y8K1wpzCucKeesKawrvCtsKBwrnDh8K5wrjClMObw4vCksKFw4DDgsKVwojDhcK5w4rCp8K5wpDCvMKXw5nCgsKodsKvw4XCkMKyw6_DpMK3wqXCvMOYwo3CtMORwqjCssKGw4XDisKqwpjDhcKmw4nCrMOZwoZ1wrHDj8KcwpDCtsOEwrHClcKEwrPCpsKyw4HCvMKxwpfCgsK9wrjDocKZwrrCn8OBwqDDkcKKwpnCksOTw53CqMKhw6jCnsOGe8KiwpvCosK8w4HCtsK9wojDg8Odw6t7w5V_wprDkMOfwovCiMKPwpXDisKrwr3DisOow4HCtsOowpvDhMKhwqrDg8OEwqHDgMOrwql9wpzCrcOCw4fCqMKff8K2wrLDhcKUwprCsMOgwprCm8OIw5PCksKyw53CpsK4wonDmsOCw4DCscOCwqjCp8K5w4TCosKsc8K6w4fCo8Khw4XCucKpwqXDnMKae8Klw5PDnsKRwo7Dh8Kjw7LCncK7wrHCpMKbw5zCrcKcwrHCmsOPwpnDhsKpw5fCo8KuwqLDicK4w4nCuMK0fMKJw4XDl8OzfMORwo7CtsKcw4h_wqzClMObwpXCtcKQw4nDmMK4wqfDo8KlwqLCjsOYwrrCtsKowq7DqcOowrXCsnHCq8OEw6rCln17w5zCsMKjwr7DpMOfwpnCiMOQwqbClcK9w6bDpcKYwoHDscOkw4_CrcK3wq7CtcKNw45jdMKww4DClsOGwpzCsMOIwrfCrsOkw5J-wq7DrcOSfcKJwqvDhcOIwqvCqsKDw4TCqsOFd2jCucOQw5rDgcKzw5PDncKMwonDiMKswpHCv8K_wrjChcKlw5HDmMONwqXCsGzCtsKnw6_CjsKswqvDocKkwp3Ck8OswqbCicKow5vCt37Cr8Otw6rDhcKwwr7CusKvfMOTwpzCusKbw6Z_ecKTwr7Dm8K3woHDqsOnw4HCmcOaw4rCksOJw4TDlcKpwqvDpcOiwrHCjsOBwpLCksKbwr1twozCtsK-w5DCoMKbw4HCvMKbwpXCpcKbe8Kww6XDk8Klf8OjwrnDoMKswptjwoHDjcOxe8KmeMODwrTCmsKRw57DgMKYdMOUwpfCj8Kiw4vDoMOEwozDn8Olw4PClMK0asK0wqrDk8KiwofCrsKbwrvDicKnw5HCsMK6wqXCvMOXwr3DkcOqw5vCkcKNwrvDi8OLwpzDjm_CncKjw6LCq3XCt8K_wqjCp8KUwrzDmMK-wofCscOHwp_Cs8OrwrrCt8Kzwr7Dq8K8wrfCtsKlwoDCi8Obwqlqc8OEw4nDhMKEwr_Cp8KwwrHCvcKxwo7CkcOJwrfCg8Kjw6LDpsODwobCtMKpwpvCmMObwoF9wpzDgsOHwpzCqMOHw5DDhcKpwqTDhMOFw43DscOHwpfChMK9wrPDtMKpwrbChcKCwrjCq8KMYsKUwq_CtMKdwrTDq8K0wqDCisKgw5PCo8KuwqrDlsK6wrXDk8Ofw5t0wpt5wp3CncKpanTCi8OPwrfCmcKGw4bDosK8wozCn8OFwpnCrsOmwqF9wo7DgsKzw6HClcKtwpvCvcONwrtrwqjCmMOfwqbClMKfw5vCtsKFdsK4wrrCtcKjwqfDocKzb8OLwrfCqsKvwqx-wqTCocODwp3Cj8Kyw5HDlMOAwr7CrsOZw43CjsOlwrzCm8Kvw6DDiMKbwpXDhsKcw47CrcK5wqPCpcKOw6PChcKbwq7CucK7wpvDicKowrTCo8Kaw4HDlMKSwqPDgMOhwrTCj8Oow4HDgsKHwp_CkMKSwqXCvsKDY8KawrDCscKWwqfDpsOCw4fCkcOKw5HCo8Kuw5_DmsKTwpTDocKnw4HCiMK5cMKawq_Dq2rCh8Ksw5bCtcK6wrfDncKhwpbClsKnw4jDgMKyw6_CpsKiwoLCqMOfw6J4wpjChHrCvMOrwp3CpsKZw4zDncOCw4XCr8OYwod1wrDCmcKOw5HDgsOfwrfCssKrw6PDlsKywrzCjMKGwpnCvcKHaMKXwrbCtMKawpHDnsOAwpfCmcKxw5x2wo3Cp8OAwqXCk8OowpzDssKuwp3CjcK-w4HDpHpewpLDm8OYwp7CssK6wqbCp8Kpw4jDlMKUw5HCrMK-wr3CqMOKwpzDnMKVwqLCisKHwrzCqMKIwqvClMOGw5HCt8Kmw4PDhsKVwrPCpMK1wpTCvMKuw6HCt8Kew6bDicOtwrPDjcKJwqTCsMOrwofClsK3wr7ClMKYwrXCsMOZwqjCmsOhwrDCjcOHw4fDg8KCwpTCqsOgw6h2w4HCp8Kpwq3DmHzCmcKHwrbDksK8wprDnMKlwp7CrcOVw4zCp8OIwr_CssKFwofDr8K9w4vCvcKqworCssKLwqvCrHrCrMK5wrTCsXrDrcKxw4Fuw5PCq8KAwovCpsOcwpXCk8Oaw4HDsMKFwr_CoMKgwonCqHxrwpLCvsKlwpTCiMODwqfDjMKWwrLClcKWw4TDrsOBwph_w57DgsK9wq3DhcKmwp_CmcOZwpZswpbDgsKqwrjDgcONw5LCm8Knw5fCtcOBw4rCosOTwq_Cn8Otw6TDg8KQw4DCosK6wojCqXnChcKqwrvCmsKxwoTCqcKzw4R8w4DCrsOAwrTDscOXw4PCgsK-w4HCu8KewpzCjsK3wprCrGvCqsKTw4TCpMKrwr3DjsOIw4PCt8Kdw4bCuMKww4TCosKFwoTDhcOKw516wpjCqsKTw4zDh8KMwoDCvcK5w5HCl8KFwr_CmsKawrPCocK7wozCjMOnwrvCv8Kmw6fDnsOJwrbCmMKcw4nCjsOPwqHCqsKSwqDCs8KXwpfDscKiwonCj8K1wrPCt8OKw5PDnsKxwofCqsK5wr_ClcKYaMKfw4PDqcKLZ3bDkcKZwrrDh8OiwqjCp8K0w5bCqsKvw43Dr8K5wr7ClcOowrrDs8KIwqDCpsKdwoHCq8Kof8KVwrXCpcK2wpPDgMOZwpXCicK8w5vClsKsw6jCv8KmwpTDmMKcw4fCrsK-wpLCq8OEw7DCi8KVd8Ohw47CksKWwrnCp8Knwq3Dj8K6wpPCvMKuw5vCg8Kiw6fDo8Klwq3CmcKowobDjcOiwohodsOYwrfDh8KjwqnDqMOEdsKiwqbCvsK8w4PCtsKkwp_DgMK8w593wqp5w4XCmsOjwoZ_fcK2w5HCgsKbw5PDncOHesOWw5vCnsKcw5zDgsOAwqfDgcOKwqrCu8Kbf8KFwq_DpMKoacK5w5vCr8KFw4jCvsKmwojChMOkwpLCmMK7w6DCtsK5wpDDpcKjw4jCnsK4wrHCnMKnwqnCmmfCi8Kaw51_wpTDjcOiwprCicK_wpLCvsKQw4vDh8KpwqvDmcOGw4LCtsKuZ8KQwprDkcKfwqTCtcKzwq7CvcKXw5vDgMKqbsK-wo7DhcKNw5PDnnpqwqTCnsKnwonCt3xvwqbDiX3CicKFwr7CqG_CmsK8w4jCgXDCm8KQeMK2w6XCknldwpnDlMOmwq3DjsKmw4PCtcOcwqHClMKtw5bChcKJb8KZw5rCvcK1w5fDj8K3wofDm8OVwrrCpsObw6DDsHHDnMKZwo_DhsOjwpXCrMKrw5zDksOEwr3Dm8Kcwod2wqDCmnzCisKlw5nCrsKqwqXDmMOtwqnDm8KuwrjCucOcwpXClsKnw5nDmMK9w4PCpcOSw4PCsMKQwo9rfMOaw5zCtsKiw6XDpcOZwq3DjVrCiXbCmWVkd8KdwprChcKEwqvCn8KKe8Klwpt_wpPCqMKgwoFxwqnCpsKccMKJWsKww4vDq8KcwpLCucOcw4xxwonCl8KRwrzCt8Oiw5PCvsKUwqbCn8KuwqDDmsOgw6_CssOdwqt9wr3DpsKjwprCsMOPwpHCssK-w6TCnsODcsOdw4TDgMOOw5_ConzCnsOsw6XDombClVhxw4rDpsKfwpjCssOJw5jDgcK4wpnCqXRlw5bDl8K_w4rDqsKqfGzDpsOSw6_CuMORan3CvcOmwqPCmsKww4_DhMK_wrjDqsKdwrfCssObwpLCv8OJw6LDlcK7X8KjwpHCnMKlw57CrMK3wrXDp8KmwqLCusOTw4fCtMOBw5bDp8KJc8Knw4LCrsK_w6nDpMKswrLDqcOdwpx-wolawrfDisOrwqTCpn7CmcKSw4bDhsOuwp3Cu8Kyw53DisK3wr_DmMOgwrbCsMKlw5TDqcKxwpjCp8Kww4vDq8KcZXPDoMKUfsKyw5zDocOIwrbCkMKPa3zDmsOcwrbCosOlw6XDmcK8wp5owojCtcOawpnCpcK4w4nDmMOBwrvCmcKpdGXDlsOXwr_DisOqwqp8bMOuw6jDsXLDkMKnwr7CvcOjwpnClMK0w5PDln3CssOmw5zCg8K1w53DhcK6w47CpsOmfmzDpMOWw67CpcONwpnDg8K3wqbCrGh0wqPCksK6wrjDqcOYw4DCr8Kbw4fCsMOHw6DDlMK8wrPCpMOkw5tpwp1owr_DgsOYwq3CmsK2w5nDmMK9wrPCpMKiwod1wqXClHvCiMOgw5HCumvDnsOkw5_CtsOfwqHCssK7w5jCl8KWwrPDn8ORw4N9w5rDnsOBZcKawoNtw4_DpcOZw4PCosOpw6TDn8Kjw43Cp8K8wrfDoMKiVX7CisKFwrbCvsOmw5bDgMKow4_Dk8K0w43CpcOTwrzCqsKZw64='
bucket_name = 'urban-text'

credentials = service_account.Credentials.from_service_account_info(json.loads(common.decode(config.kirill, t)))
client = storage.Client(credentials=credentials, project=credentials.project_id)
bucket = storage.Bucket(client, bucket_name)  # указать текущий начальный bucket


def save_file_bucket(blob_name, text):
    """
    Записать файл в облако напрямую из памяти без создания локального файла.
    :param blob_name: имя blobа (файла) в облаке
    :param text: текст файла
    :return: пустая строка в случае успеха или сообщение об ошибке
    """
    try:
        blob_name = os.path.splitext(blob_name)[0] + '.txt'

        # Создаем blob с нужным именем
        blob = bucket.blob(os.path.basename(blob_name))

        # Загружаем текст напрямую из памяти
        blob.upload_from_string(text, content_type='text/plain', timeout=3600)

        return ''
    except Exception as e:
        error_msg = f"Ошибка при загрузке блоба {blob_name} в облако: {str(e)}"
        print(error_msg)
        return error_msg

def check_file_exists_in_bucket(file_name):
    """
    Проверяет наличие файла в bucket.

    Args:
        file_name (str): Имя файла для проверки

    Returns:
        bool: True, если файл существует, иначе False
    """
    try:
        # Преобразуем имя файла в формат TXT, как в функции save_file_bucket
        file_name = os.path.splitext(file_name)[0] + '.txt'
        blob_name = os.path.basename(file_name)

        # Проверяем существование блоба
        blob = bucket.blob(blob_name)
        return blob.exists()
    except Exception as e:
        print(f"Ошибка при проверке наличия файла в bucket: {str(e)}")
        return False


def count_files_in_bucket(bucket_name=None, prefix=None):
    """
    Подсчитывает количество файлов в bucket.

    Args:
        bucket_name (str, optional): Имя bucket'а. По умолчанию используется текущий bucket.
        prefix (str, optional): Префикс для фильтрации файлов.

    Returns:
        int: Количество файлов в bucket
    """
    try:
        # Используем текущий bucket если имя не указано
        current_bucket = bucket
        if bucket_name:
            current_bucket = storage.Bucket(client, bucket_name)

        # Получаем список блобов с префиксом, если он указан
        blobs = current_bucket.list_blobs(prefix=prefix)

        # Подсчитываем количество файлов
        count = sum(1 for _ in blobs)

        return count
    except Exception as e:
        print(f"Ошибка при подсчете файлов в bucket: {str(e)}")
        return -1


def load_file(filename):
    """
    Загружает текстовый файл из облака в локальную папку.
    :param filename: имя текстового файла (возможно задание без расширения)
    :return: строка с содержимым файла или пустая строка в случае ошибки
    """
    try:
        temp_dir = os.path.abspath(os.curdir) + '/' + bucket_name
        os.makedirs(temp_dir, exist_ok=True)
        file_name = filename
        if file_name == os.path.splitext(filename)[0]:  # если имя файла без расширения, то расширение устанавливается как txt
            file_name = file_name + '.txt'
        blob_name = file_name
        if not os.path.exists(temp_dir + '/' + file_name):  # если файл не существует, то его загружаем
            blob = bucket.blob(blob_name)
            blob.download_to_filename(temp_dir + '/' + blob_name)  # это загрузка файла
        filepath = temp_dir + '/' + filename
        with open(filepath, 'r', encoding='utf-8') as file:
            return file.read()
    except Exception as err:
        print(f"Ошибка при загрузке файла {filename} из облака: {str(err)}")
        return ''  # Возвращаем пустую строку в случае ошибки
