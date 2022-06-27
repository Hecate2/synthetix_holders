from gevent import monkey
monkey.patch_all()
from gevent.pool import Pool, Greenlet
from gevent.queue import Queue
import gevent

from typing import Tuple, List, Dict
import traceback
from dateutil.parser import isoparse
from retry import retry
from web3 import Web3
import requests
from sqlalchemy.orm import Session
from models import Balance, engine

w3 = Web3(Web3.HTTPProvider('https://rpc.ankr.com/eth'))
session = requests.Session()

tokens = {
    '0xd2dF355C19471c8bd7D8A3aa27Ff4e26A21b4076': 'sAAVE',
    '0xF48e200EAF9906362BB1442fca31e0835773b8B4': 'sAUD',
    '0xfE18be6b3Bd88A2D2A7f928d00292E7a9963CfC6': 'sBTC',
    '0xe36E2D3c7c34281FA3bC737950a68571736880A1': 'sADA',
    '0xbBC455cb4F1B9e4bFC4B73970d360c8f032EfEE6': 'sLINK',
    '0x104eDF1da359506548BFc7c25bA1E28C16a70235': 'sETHBTC',
    '0x5e74C9036fb86BD7eCdcb084a0673EFc32eA31cb': 'sETH',
    '0xD71eCFF9342A5Ced620049e616c5035F1dB98620': 'sEUR',
    '0xF6b1C627e95BFc3c1b4c9B825a032Ff0fBf3e07d': 'sJPY',
    '0x1715AC0743102BF5Cd58EfBB6Cf2dC2685d967b6': 'sDOT',
    '0x97fe22E7341a0Cd8Db6F6C021A24Dc8f4DAD855F': 'sGBP',
    '0x269895a3dF4D73b077Fc823dD6dA1B95f72Aaf9B': 'sKRW',
    '0x0F83287FF768D1c1e17a42F44d644D7F22e8ee1d': 'sCHF',
    '0xC011a73ee8576Fb46F5E1c5751cA3B9Fe0af2a6F': 'SNX',
    '0x57Ab1ec28D129707052df4dF418D58a2D46d5f51': 'sUSD',
}
api_key = 'ckey_14af216ed1364858896c0f731dd'

RequestExceptions = (
    requests.RequestException,
    requests.ConnectionError,
    requests.HTTPError,
    requests.Timeout,
)


def get_all_holders_of_token_at_block_height(token_address: str, block_height: int = 0):
    if block_height == 0:
        block_height = int(w3.eth.block_number)
    
    @retry(RequestExceptions, tries=3)
    def get_one_page_of_holders(page_num: int, page_size: int = 50) -> Tuple[List[Dict], str, bool]:
        r = session.get(
            f'https://api.covalenthq.com/v1/1/tokens/{token_address}/token_holders/?key={api_key}&block-height={block_height}&page-number={page_num}&page-size={page_size}')
        if r.status_code != 200:
            r.raise_for_status()
        r = r.json()
        if r['error']:
            raise requests.RequestException(f"""{r['error_code']} {r['error_message']}""")
        r = r['data']
        return (r['items'],
                r['updated_at'],
                r['pagination']['has_more'])
        # [{'contract_decimals': 18, 'contract_name': 'ConstitutionDAO', 'contract_ticker_symbol': 'PEOPLE', 'contract_address': '0x7a58c0be72be218b41c608b7fe7c5bb630736c71', 'supports_erc': None, 'logo_url': 'https://logos.covalenthq.com/tokens/1/0x7a58c0be72be218b41c608b7fe7c5bb630736c71.png', 'address': '0xf977814e90da44bfa03b6295a0616a897441acec', 'balance': '1450000000000000000000000000', 'total_supply': '5066696281617111949811867230', 'block_height': 15032597}, ... ]
        # '2022-06-27T04:51:29.741094923Z'
        # True or False
    
    def save_data(items: List[Dict], timestamp: str):
        with Session(engine) as db_session:
            for item in items:
                db_session.add(Balance(id=None, timestamp=isoparse(timestamp), **{_: item[_] for _ in dir(Balance) if not _.startswith('_') and _ in item}))
            db_session.commit()
    
    def get_all_holders_and_save():
        page_num = 0
        initial_page_num = 0
        pool = Pool(5)
        db_pool = Pool(5)
        queue = Queue(pool.size)
        for initial_page_num in range(pool.size):
            task = pool.spawn(get_one_page_of_holders, initial_page_num)
            queue.put(task)
        while 1:
            has_more = False
            try:
                task: Greenlet = queue.get()
                task.join()
                items, timestamp, has_more = task.value
                if items:
                    db_pool.spawn(save_data, items, timestamp)
                    print(f"""Finished {token_address} page num {page_num}; {items[0]['contract_ticker_symbol']}""")
                    page_num += 1
            except Exception as e:
                print(traceback.print_exc())
                print(f"""Failed! {token_address} page num {page_num}""")
            if has_more:
                task = pool.spawn(get_one_page_of_holders, initial_page_num)
                initial_page_num += 1
                queue.put(task)
            else:
                pool.kill()
                db_pool.join()
                break
    
    get_all_holders_and_save()


if __name__ == '__main__':
    block_height = w3.eth.block_number
    print(f'block height: {block_height}')
    # for token in tokens:
    #     get_all_holders_of_token_at_block_height(token, block_height=block_height)
    tasks = [gevent.spawn(get_all_holders_of_token_at_block_height, token, block_height=block_height) for token in tokens]
    gevent.joinall(tasks)
