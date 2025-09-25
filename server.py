"""
FastMCP base example.

"""
import logging
import sys
from mcp.server.fastmcp import FastMCP

# Create an MCP server
mcp = FastMCP("Demo")

# Add a steps to miles tool
@mcp.tool()
def steps_to_miles(steps: int) -> float:
    """
    Convert steps to miles

    Args:
        steps (int): Number of steps
    Returns:
        float: Number of miles
    """
    return steps / 2000.0

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    try:
        logger.info("Starting MCP server (stdio)")
        mcp.run("stdio")
    except KeyboardInterrupt:
        logger.info("KeyboardInterrupt received — shutting down cleanly")
        sys.exit(0)