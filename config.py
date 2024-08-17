BOT_API_TOKEN = "7267987681:AAH0Aw5u_zsnNUUsdl_Bhb1M_dttyjANPwk"

LINK_TO_WEBSITE = "https://link2website.example"
LINK_TO_SUBSCRIBE = "https://link2sub.example"

SUPPORT_UID = "661081972"
SUPPORT_USERNAME = "S7459N"
LINK_TO_SUPPORT = f"https://t.me/{SUPPORT_USERNAME}"

SERVER_HOST_IP = '127.0.0.1'
SERVER_HOST_PORT = 8887

PROXIES_PER_USER = 80
TEMP_WALLET_EXPIRE_SECONDS = 60

SUB_COST_MONTH = 240
SUB_COST_DAY = SUB_COST_MONTH / 30.0

RPC_CONFIG = {
    'ethereum': {
        'rpcs': [
            'https://ethereum-rpc.publicnode.com',
            'https://rpc.mevblocker.io',
            'wss://eth.drpc.org'
        ],
        'tokens': [
            "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
            "0xdAC17F958D2ee523a2206206994597C13D831ec7",
        ]
    },

    'arbitrum': {
        'rpcs': [
            'wss://arbitrum-one-rpc.publicnode.com',
            'https://endpoints.omniatech.io/v1/arbitrum/one/public',
            'https://arbitrum.meowrpc.com'
        ],
        'tokens': []
    },

    'optimism': {
        'rpcs': [
            'https://optimism.llamarpc.com',
            'wss://optimism-rpc.publicnode.com',
            'https://endpoints.omniatech.io/v1/op/mainnet/public'
        ],
        'tokens': []
    },

    'bsc': {
        'rpcs': [
            'https://bsc-pokt.nodies.app',
            'wss://bsc-rpc.publicnode.com',
            'https://bsc.drpc.org'
        ],
        'tokens': []
    },
}