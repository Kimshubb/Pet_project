import re

text = """
TTrraannssaaccttiioonn DDeettaaiillss PPaayymmeenntt rreeffeerreennccee VVaalluuee DDaattee CCrreeddiitt ((MMoonneeyy IInn)) DDeebbiitt ((MMoonneeyy OOuutt)) BBaallaannccee
MIREMA DRUG T-BY:/403814908430/07-02-2024 11:49
S1752882 07/02/2024 6,100.00 83,096.23
627851XXXXXX3207
PAYED BY:BRIAN MWANGU/364928949298/07-02-2024 17:1
364928949298 54393044 07/02/2024 4,400.00 87,496.23
364928949298
MPS 254712647662 SB72EPJ3CO 447856# CHARLES KAMAU
rUQu0eAwpDcB S3104833 07/02/2024 600.00 88,096.23
rUQu0eAwpDcB
MPS 254742367656 SB82FAY6XO 447856# Catherine Nzil
XjgRPnM4Dw8W S3345701 08/02/2024 2,000.00 90,096.23
XjgRPnM4Dw8W
MPS 254791030616 SB95JF3U21 447856# DAVID NGATIA W
iDaBV6ZR21sT S5557787 09/02/2024 2,000.00 92,096.23
iDaBV6ZR21sT
MPS 254708237010 SB99KKW4GR 447856# EUNICE WAMBUI
lhvnwy8IGHLq S6246958 09/02/2024 1,000.00 93,096.23
lhvnwy8IGHLq
APP/STANLEY KIMANI KINYANJUI/
707560688525 54224081 10/02/2024 50,000.00 43,096.23
707560688525
SMS CHARGE
707560688525 54224081 10/02/2024 02.26 43,093.97
707560688525
MPS 254706334824 SBB4T40060 447856# STEPHEN NGUGI
iJC0g2OPuAmz S293946 11/02/2024 700.00 43,793.97
iJC0g2OPuAmz
MPS 254714644939 SBC0TDKCAQ 447856# ABEL KITHUKA M
Bvd3fiR4brQj S369951 12/02/2024 150.00 43,943.97
Bvd3fiR4brQj
MPS 254715561574 SBC8TH9EOK 447856# DAN OTIENO OBO
Wg9heLGAbpsC S435175 12/02/2024 900.00 44,843.97
Wg9heLGAbpsC
MPS 254746319181 SBC3TJYY7F 447856# Edith Nafula s
aYr9140LsoCA S473181 12/02/2024 1,000.00 45,843.97
aYr9140LsoCA
MPS 254727238868 SBD8WTV12I 447856# STEPHEN MUTAVI
FV2bw5tO4Qks S2372235 13/02/2024 1,000.00 46,843.97
FV2bw5tO4Qks
MPS 254792953731 SBD8WVKL2C 447856# GRACE WANJIRU
xOwYqDSjUM5I S2393390 13/02/2024 3,000.00 49,843.97
xOwYqDSjUM5I
MPS 254791440641 SBD0WWVUBO 447856# esther wambui
7dnBOJCc5WX9 S2411138 13/02/2024 500.00 50,343.97
7dnBOJCc5WX9
Disclaimer: This record is produced for your personal use and is not transferable.Contact us for 24 hours assistance on +254 763 000 000 or email
info@equitybank.co.ke *****COMPUTER GENERATED STATEMENT
09/03/2024 Page 8/14
"""

# Regex for Mpesa transactions
mpesa_regex = r"MPS\s254\d{9}\s([A-Z0-9]{10})\s\d{2}/\d{2}/\d{4}\s(\d{1,3}(,\d{3})*\.\d{2})"

# Regex for Bank transactions
bank_regex = r"/(\d{12})/\d{2}-\d{2}-\d{4}\s(\d{1,3}(,\d{3})*\.\d{2})"

# Find all Mpesa transactions
mpesa_matches = re.findall(mpesa_regex, text)
for match in mpesa_matches:
    transaction_code, amount = match[0], match[1]
    print(f"Mpesa Transaction Code: {transaction_code}, Amount: {amount}")

# Find all Bank transactions
bank_matches = re.findall(bank_regex, text)
for match in bank_matches:
    transaction_code, amount = match[0], match[1]
    print(f"Bank Transaction Code: {transaction_code}, Amount: {amount}")


