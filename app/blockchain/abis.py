ERC20_ABI = [
    {
        "anonymous": False,
        "inputs": [
            {
                "indexed": True,
                "name": "from",
                "type": "address",
            },
            {
                "indexed": True,
                "name": "to",
                "type": "address",
            },
            {
                "indexed": False,
                "name": "value",
                "type": "uint256",
            },
        ],
        "name": "Transfer",
        "type": "event",
    },
    {
        "inputs": [
            {
                "name": "account",
                "type": "address",
            }
        ],
        "name": "balanceOf",
        "outputs": [
            {
                "name": "",
                "type": "uint256",
            }
        ],
        "stateMutability": "view",
        "type": "function",
    },
]


ERC1155_ABI = [
    {
        "anonymous": False,
        "inputs": [
            {
                "indexed": True,
                "name": "operator",
                "type": "address",
            },
            {
                "indexed": True,
                "name": "from",
                "type": "address",
            },
            {
                "indexed": True,
                "name": "to",
                "type": "address",
            },
            {
                "indexed": False,
                "name": "id",
                "type": "uint256",
            },
            {
                "indexed": False,
                "name": "value",
                "type": "uint256",
            },
        ],
        "name": "TransferSingle",
        "type": "event",
    },
    {
        "anonymous": False,
        "inputs": [
            {
                "indexed": True,
                "name": "operator",
                "type": "address",
            },
            {
                "indexed": True,
                "name": "from",
                "type": "address",
            },
            {
                "indexed": True,
                "name": "to",
                "type": "address",
            },
            {
                "indexed": False,
                "name": "ids",
                "type": "uint256[]",
            },
            {
                "indexed": False,
                "name": "values",
                "type": "uint256[]",
            },
        ],
        "name": "TransferBatch",
        "type": "event",
    },
    {
        "inputs": [
            {
                "name": "account",
                "type": "address",
            },
            {
                "name": "id",
                "type": "uint256",
            },
        ],
        "name": "balanceOf",
        "outputs": [
            {
                "name": "",
                "type": "uint256",
            }
        ],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [
            {
                "name": "accounts",
                "type": "address[]",
            },
            {
                "name": "ids",
                "type": "uint256[]",
            },
        ],
        "name": "balanceOfBatch",
        "outputs": [
            {
                "name": "",
                "type": "uint256[]",
            }
        ],
        "stateMutability": "view",
        "type": "function",
    },
]
