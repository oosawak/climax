# 1. PPAを追加するツールをインストール
sudo apt update
sudo apt install -y software-properties-common

# 2. Neovim公式の最新安定PPAを追加
sudo add-apt-repository ppa:neovim-ppa/unstable
sudo apt update

# 3. インストール
sudo apt install -y neovim


# AIプラグインのビルドや検索・パースに必要なツール群
sudo apt install -y git make cmake g++ unzip ripgrep fd-find

# 設定ディレクトリを作成
mkdir -p ~/.config/nvim

# メインの設定ファイルを作成
touch ~/.config/nvim/init.lua


