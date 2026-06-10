-- ====================================================================
-- 1. 基礎設定
-- ====================================================================
vim.g.mapleader = " "         -- リーダーキーを【スペースキー】に設定
vim.opt.number = true          -- 行番号を表示
vim.opt.relativenumber = true  -- 相対行番号を表示
vim.opt.clipboard = "unnamedplus" -- クリップボードをOSと共有
vim.opt.smartindent = true     -- スマートインデント

-- ====================================================================
-- 2. プラグインマネージャー (lazy.nvim) の自動インストール
-- ====================================================================
local lazypath = vim.fn.stdpath("data") .. "/lazy/lazy.nvim"
if not (vim.uv or vim.loop).fs_stat(lazypath) then
  vim.fn.system({
    "git", "clone", "--filter=blob:none",
    "https://github.com/folke/lazy.nvim.git", "--branch=stable", lazypath,
  })
end
-- ★【修正箇所】preload ではなく prepend が正しいメソッドです
vim.opt.rtp:prepend(lazypath)

-- ====================================================================
-- 3. プラグインの設定（avante.nvim とその仲間たち）
-- ====================================================================
require("lazy").setup({
  -- UIアイコン
  { 'nvim-tree/nvim-web-devicons' },

  -- 履歴の選択画面などで使うファジーファインダー
  {
    'nvim-telescope/telescope.nvim',
    dependencies = { 'nvim-lua/plenary.nvim' }
  },

  -- avante.nvim
  {
    "yetone/avante.nvim",
    event = "VeryLazy",
    lazy = false,
    version = false,
    opts = {
      provider = "azure", 
      azure = {
        endpoint = "https://openai-climax.openai.azure.com/", -- エンドポイントURL
        deployment_name = "open-climax", -- デプロイ名（例: gpt-4o-deploy）
--        api_version = "2024-06-01", -- 使用するAPIバージョン
        api_version = "2025-04-01-preview", -- 使用するAPIバージョン
        timeout = 30000,
        temperature = 0,
        max_tokens = 4096,
      },

--      provider = "anthropic", 
--      anthropic = {
--        endpoint = "https://api.anthropic.com",
--        model = "claude-3-5-sonnet", -- もしくは最新の claude-3-7-sonnet
--        timeout = 30000,
--        temperature = 0,
--        max_tokens = 4096,
--      },
      mappings = {
        ask = "<leader>aa",       -- スペース + a + a でチャット開始
        edit = "<leader>ae",      -- 選択したコードを スペース + a + e で部分修正
        refresh = "<leader>ar",
      },
    },
    build = "make",
    dependencies = {
      "nvim-treesitter/nvim-treesitter",
      "stevearc/dressing.nvim",
      "nvim-lua/plenary.nvim",
      "MunifTanjim/nui.nvim",
      "MeanderingProgrammer/render-markdown.nvim",
    },
  }
})

-- ====================================================================
-- 1. 基礎設定（お好みでカスタマイズしてください）
-- ====================================================================
vim.g.mapleader = " " -- クリップボードやAIを呼び出す「リーダーキー」を【スペースキー】に設定
vim.opt.number = true  -- 行番号を表示
vim.opt.relativenumber = true -- 相対行番号を表示（Vimの移動が楽になります）
vim.opt.clipboard = "unnamedplus" -- クリップボードをOSと共有
vim.opt.smartindent = true -- スマートインデント

-- ====================================================================
-- 2. プラグインマネージャー (lazy.nvim) の自動インストール
-- ====================================================================
local lazypath = vim.fn.stdpath("data") .. "/lazy/lazy.nvim"
if not vim.loop.fs_stat(lazypath) then
  vim.fn.system({
    "git", "clone", "--filter=blob:none",
    "https://github.com/folke/lazy.nvim.git", "--branch=stable", lazypath,
  })
end
vim.opt.rtp:preload(lazypath)

-- ====================================================================
-- 3. プラグインの設定（ここにavante.nvimとその依存関係を記述）
-- ====================================================================
require("lazy").setup({
  -- UIを綺麗にするためのアイコン（必須ではないですが推奨）
  { 'nvim-tree/nvim-web-devicons' },

  -- ファジーファインダー（AIのセッション切り替え等で綺麗なUIを使うため）
  {
    'nvim-telescope/telescope.nvim',
    dependencies = { 'nvim-lua/plenary.nvim' }
  },

  -- 本命：avante.nvim (AIペアプログラマ)
  {
    "yetone/avante.nvim",
    event = "VeryLazy",
    lazy = false,
    version = false, -- 常に最新の機能を使うためにfalseを推奨
    opts = {
      -- デフォルトのAIプロバイダーを設定（anthropic, openai, gemini など）
      -- 独自のキーバインド（競合を避ける設定）
      mappings = {
        ask = "<leader>aa",       -- スペース + a + a でAIチャットを開く
        edit = "<leader>ae",      -- コードを選択して スペース + a + e でインライン修正
        refresh = "<leader>ar",   -- チャットのリフレッシュ
      },
    },
    -- avanteが内部でビルドを走らせるための設定
    build = "make",
    dependencies = {
      "nvim-treesitter/nvim-treesitter",
      "stevearc/dressing.nvim",
      "nvim-lua/plenary.nvim",
      "MunifTanjim/nui.nvim",
      --- 以下の3つはavanteのインライン差分（パッチ）表示を美しくするために必要
      "MeanderingProgrammer/render-markdown.nvim",
    },
  }
})
