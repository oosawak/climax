# Source this from your tm launcher or tmux config.
# Example:
#   source-file /home/oosawak/Workspace/climax/tools/tmux_usage_status_bar.tmux
set -g status-right "#(python3 /home/oosawak/Workspace/climax/tools/tmux_usage_status_bar.py)"
