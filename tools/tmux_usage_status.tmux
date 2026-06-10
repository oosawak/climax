# Source this from your tm or tmux startup path.
# Example:
#   source-file /home/oosawak/Workspace/climax/tools/tmux_usage_status.tmux
set -g status-right "#(python3 /home/oosawak/Workspace/climax/tools/tmux_usage_status.py)"
