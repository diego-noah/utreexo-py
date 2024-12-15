class NetworkError(Exception):
    """Custom exception for invalid network type."""
    def __init__(self, n_type: str):
        self.n_type = n_type
        super().__init__(f"Invalid/not supported net flag given: {n_type}")

def err_invalid_network(n_type: str) -> NetworkError:
    """Function to raise an error for invalid network type."""
    return NetworkError(n_type)

try:
    network_type = "XYZ"
    if network_type not in ["TCP", "UDP"]:
        raise err_invalid_network(network_type)
except NetworkError as e:
    print(f"Error: {e}")
