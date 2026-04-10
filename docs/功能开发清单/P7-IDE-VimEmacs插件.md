# P7-IDE-Vim/Emacs插件 开发分析文档

## 基本信息

| 字段 | 内容 |
|------|------|
| **优先级** | P7 |
| **功能模块** | IDE (集成开发环境) |
| **功能名称** | Vim/Emacs 插件 |
| **文档版本** | 1.0.0 |
| **创建日期** | 2026-04-10 |
| **预计工时** | 约 2-3 周 |

---

## 1. 功能概述

为 Vim 和 Emacs 用户提供 ZhC 语言支持，包括语法高亮、缩进、语法检查和基本 IDE 功能。

### 1.1 核心目标

- 语法高亮
- 自动缩进
- 语法检查 (通过 Language Server)
- 基本补全支持

---

## 2. 详细设计

### 2.1 Vim 插件架构

```
zhc-vim/
├── autoload/zhc/
│   ├── syntax.vim           # 语法高亮
│   ├── indent.vim           # 缩进规则
│   ├── ftdetect.vim         # 文件类型检测
│   └── lsp.vim             # LSP 客户端配置
├── plugin/zhc.vim          # 主插件文件
├── syntax/zhc.vim          # 语法定义
└── README.md
```

### 2.2 Vim 语法文件

```vim
" syntax/zhc.vim
" ZhC Syntax Highlighting for Vim

if exists("b:current_syntax")
  finish
endif

let b:current_syntax = "zhc"

" 关键词
syn keyword zhcKeyword 如果 则 否则 结束 对于 从 到 执行 当 返回
syn keyword zhcKeyword 函数 结构体 枚举 导入 命名空间 常量的 变量的
syn keyword zhcKeyword 新建 空 遍历 中断 继续 断言

" 类型
syn keyword zhcType 整数型 长整数型 浮点型 双精度型 字符型 布尔型
syn keyword zhcType 字符串型 空类型 指针型 数组型

" 字符串
syn region zhcString start=/"/ skip=/\\"/ end=/"/ contains=zhcEscape
syn match zhcEscape contained /\\[nrt\\"]/
syn match zhcEscape contained /\\u[0-9a-fA-F]{4}/

" 注释
syn match zhcComment "//.*$" contains=zhcTodo
syn match zhcTodo contained /\(TODO\|FIXME\|XXX\):/"

" 数字
syn match zhcNumber /\<\d\+\.\d\+\([eE][+-]\=\d\+\)\=[fF]\=>/
syn match zhcNumber /\<\d\+[eE][+-]\=\d\+\>/
syn match zhcNumber /\<\d\+\>/
syn match zhcNumber /0x[0-9a-fA-F]\+\>/

" 函数调用
syn match zhcFunction /\([\u4e00-\u9fa5_a-zA-Z][\u4e00-\u9fa5_a-zA-Z0-9]*\)\s*(/lc=1

" 高亮链接
hi def link zhcKeyword    Keyword
hi def link zhcType        Type
hi def link zhcString      String
hi def link zhcComment     Comment
hi def link zhcNumber      Number
hi def link zhcFunction    Function
hi def link zhcTodo       Todo
```

### 2.3 Vim 缩进文件

```vim
" indent/zhc.vim
" ZhC Indentation for Vim

if exists("b:did_indent")
  finish
endif
let b:did_indent = 1

setlocal indentexpr=ZhCIndent()
setlocal indentkeys+=如果,则,否则,结束,对于,执行,函数,结构体,枚举

function! ZhCIndent()
  let lnum = prevnonblank(v:lnum - 1)
  let line = getline(lnum)
  let ind = indent(lnum)

  " 增加缩进
  if line =~ '\(如果\|对于\|函数\|结构体\|枚举\)\s*('
    let ind += &shiftwidth
  endif

  " 减少缩进
  if getline(v:lnum) =~ '^\s*\(结束\|否则\)'
    let ind -= &shiftwidth
  endif

  " 保持当前行的相对缩进
  let curr_line = getline(v:lnum)
  if curr_line =~ '^\s*则\s*$'
    let ind += &shiftwidth
  endif
  if curr_line =~ '^\s*到\s*$'
    let ind += &shiftwidth
  endif

  return ind
endfunction
```

### 2.4 Emacs 插件架构

```
zhc-emacs/
├── zhc-mode.el            # 主模式定义
├── zhc-syntax.el          # 语法高亮
├── zhc-indent.el          # 缩进
├── zhc-imenu.el           # 符号大纲
├── zhc-company.el         # Company 补全
└── README.md
```

### 2.5 Emacs 主模式

```elisp
;;; zhc-mode.el --- ZhC major mode for Emacs

(require 'syntax)
(require 'font-lock)

(defvar zhc-mode-map
  (let ((map (make-keymap)))
    (define-key map "\C-c\C-b" 'zhc-visit-buffer)
    (define-key map "\C-c\C-c" 'zhc-compile)
    map)
  "Keymap for ZhC mode")

(defvar zhc-mode-syntax-table
  (let ((st (make-syntax-table)))
    ;; 字符串
    (modify-syntax-entry ?\" "\"" st)
    ;; 注释
    (modify-syntax-entry ?/ ". 12" st)
    (modify-syntax-entry ?\n ">" st)
    ;; 标识符
    (modify-syntax-entry ?_ "w" st)
    st)
  "Syntax table for ZhC mode")

(defvar zhc-font-lock-keywords
  `(
    ;; 关键词
    (,(rx (or "如果" "则" "否则" "结束" "对于" "从" "到" "执行"
             "当" "返回" "函数" "结构体" "枚举" "导入" "命名空间"))
     . font-lock-keyword-face)

    ;; 类型
    (,(rx (or "整数型" "长整数型" "浮点型" "双精度型" "字符型"
             "布尔型" "字符串型" "空类型" "指针型"))
     . font-lock-type-face)

    ;; 函数定义
    (,(rx bol (one-or-more (any space))
         (group (one-or-more (not (any "(\n"))))
         (one-or-more (any space)) "(")
     1 font-lock-function-name-face)

    ;; 数字
    (,(rx (or (group (1+ digit) "." (1+ digit)
                 (optional (any "fF")))
             (group (1+ digit))
             (group "0x" (1+ (any hex-digit)))))
     . font-lock-constant-face)
    ))

(define-derived-mode zhc-mode prog-mode "ZhC"
  "Major mode for editing ZhC source files."
  :syntax-table zhc-mode-syntax-table
  (setq font-lock-defaults '(zhc-font-lock-keywords))
  (setq-local comment-start "//")
  (setq-local comment-end "")
  (setq-local indent-line-function 'zhc-indent-line))

(defun zhc-indent-line ()
  "Indent line for ZhC mode."
  (let ((indent (calculate-zhc-indent)))
    (when (integerp indent)
      (indent-line-to indent))))

(defun calculate-zhc-indent ()
  "Calculate the indent for the current line."
  (save-excursion
    (beginning-of-line)
    (let ((indent 0))
      (while (and (not (bobp))
                  (progn (forward-line -1)
                         (beginning-of-line)
                         (or (looking-at "\\s-*//")
                             (looking-at "\\s-*$")))))
      (when (not (bobp))
        (end-of-line)
        (when (looking-at "\\(如果\\|对于\\|函数\\|结构体\\|枚举\\)")
          (setq indent (+ indent 4))))
      indent)))

(provide 'zhc-mode)

;;; zhc-mode.el ends here
```

---

## 3. LSP 集成

### 3.1 Vim LSP 配置

```vim
" autoload/zhc/lsp.vim
function! s:setup_lsp() abort
    if exists('g:loaded_lsp')
        " 使用 vim-lsp
        if executable('zhclang')
            au User lsp_setup call lsp#register_server({
                \ 'name': 'zhclang',
                \ 'cmd': {server_info->['zhclang', '--lsp']},
                \ 'whitelist': ['zhc'],
                \ 'initialization_options': {
                    \ 'settings': {
                        \ 'zhc': {
                            \ 'trace.server': 'off'
                        \ }
                    \ }
                \ },
                \ 'handlers': {
                    \ 'textDocument/publishDiagnostics': function('lsp#handlers#show_diagnostics'),
                \ }
            \ })
        endif
    endif
endfunction
```

### 3.2 Company 补全

```elisp
;;; zhc-company.el --- Company backend for ZhC

(require 'company)
(require 'cl-lib)

(defvar zhc-keywords
  '("如果" "则" "否则" "结束" "对于" "从" "到" "执行"
    "当" "返回" "函数" "结构体" "枚举" "导入" "命名空间"
    "整数型" "长整数型" "浮点型" "双精度型" "字符型"
    "布尔型" "字符串型" "空类型" "指针型" "新建" "空"))

(defun company-zhc-backend (command &optional arg &rest ignored)
  "Company backend for ZhC language."
  (cl-case command
    (prefix (and (eq major-mode 'zhc-mode)
                 (company-grab-symbol)))
    (candidates
     (cl-remove-if-not
      (lambda (c) (string-prefix-p arg c))
      zhc-keywords))
    (sorted t)
    (duplicates t)))

(add-to-list 'company-backends 'company-zhc-backend)

(provide 'zhc-company)
```

---

## 4. 安装和使用

### 4.1 Vim 安装

```bash
# 使用 vim-plug
Plug 'zhc-team/zhc-vim'

# 或手动安装
# 将插件目录复制到 ~/.vim/
```

### 4.2 Emacs 安装

```elisp
;; use-package 配置
(use-package zhc-mode
  :ensure t
  :mode ("\\.zhc\\'" . zhc-mode)
  :hook (zhc-mode . company-mode))
```
