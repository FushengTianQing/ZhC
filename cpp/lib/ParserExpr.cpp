//===--- ParserExpr.cpp - Expression Parsing (Pratt Parser) ------------------===//
//
// This file implements expression parsing using Pratt parsing (precedence climbing)
// for the ZhC parser.
//
//===----------------------------------------------------------------------===//

#include "zhc/Parser.h"
#include "zhc/ASTContext.h"

#include "llvm/Support/raw_ostream.h"

namespace zhc {

//===----------------------------------------------------------------------===//
// Expressions (Pratt Parser)
//===----------------------------------------------------------------------===//

int Parser::getPrecedence(TokenKind kind) {
  switch (kind) {
    case TokenKind::equal:       return 2;   // Assignment
    case TokenKind::pluseq:
    case TokenKind::minuseq:
    case TokenKind::stareq:
    case TokenKind::slasheq:     return 2;
    case TokenKind::logical_or:  return 3;
    case TokenKind::logical_and: return 4;
    case TokenKind::eq:
    case TokenKind::neq:         return 5;
    case TokenKind::lt:
    case TokenKind::gt:
    case TokenKind::le:
    case TokenKind::ge:          return 6;
    case TokenKind::plus:
    case TokenKind::minus:       return 7;
    case TokenKind::star:
    case TokenKind::slash:
    case TokenKind::percent:     return 8;
    case TokenKind::amp:
    case TokenKind::pipe:
    case TokenKind::caret:       return 8;
    case TokenKind::shl:
    case TokenKind::shr:         return 9;
    default:                     return -1;
  }
}

std::unique_ptr<ExprNode> Parser::parseExpression(int minPrec) {
  auto left = parseUnaryExpr();
  if (!left) return nullptr;

  while (true) {
    int prec = getPrecedence(CurrentToken.Kind);
    if (prec < minPrec) break;

    TokenKind op = CurrentToken.Kind;
    advance();

    // Handle assignment specially (right-associative)
    int nextPrec = prec;
    if (op == TokenKind::equal || op == TokenKind::pluseq ||
        op == TokenKind::minuseq || op == TokenKind::stareq ||
        op == TokenKind::slasheq) {
      nextPrec = prec;  // Right-associative
    } else {
      nextPrec = prec + 1;  // Left-associative
    }

    auto right = parseExpression(nextPrec);
    if (!right) break;

    if (op == TokenKind::equal || op == TokenKind::pluseq ||
        op == TokenKind::minuseq || op == TokenKind::stareq ||
        op == TokenKind::slasheq) {
      left = std::make_unique<AssignExpr>(op, std::move(left), std::move(right));
    } else {
      left = std::make_unique<BinaryOperatorExpr>(op, std::move(left), std::move(right));
    }
  }

  return left;
}

std::unique_ptr<ExprNode> Parser::parseUnaryExpr() {
  // Prefix operators
  switch (CurrentToken.Kind) {
    case TokenKind::minus:
    case TokenKind::logical_not:
    case TokenKind::tilde:
    case TokenKind::plus: {
      TokenKind op = CurrentToken.Kind;
      advance();
      auto operand = parseUnaryExpr();
      return std::make_unique<UnaryExpr>(op, std::move(operand), true);
    }
    default:
      break;
  }

  return parsePostfixExpr();
}

std::unique_ptr<ExprNode> Parser::parsePostfixExpr() {
  auto expr = parsePrimaryExpr();

  while (true) {
    switch (CurrentToken.Kind) {
      case TokenKind::lparen: {
        // Function call
        advance();
        llvm::SmallVector<std::unique_ptr<ExprNode>, 4> args;
        if (!consumeIf(TokenKind::rparen)) {
          do {
            args.push_back(parseExpression());
          } while (consumeIf(TokenKind::comma));
          expect(TokenKind::rparen);
        }
        expr = std::make_unique<CallExpr>(std::move(expr), std::move(args));
        break;
      }
      case TokenKind::dot: {
        advance();
        if (CurrentToken.Kind != TokenKind::IDENTIFIER) {
          DiagEngine.report(getCurrentLocation(), DiagID::err_expected_identifier);
          break;
        }
        llvm::StringRef member = CurrentToken.Spelling;
        advance();
        expr = std::make_unique<MemberExpr>(std::move(expr), member, false);
        break;
      }
      case TokenKind::arrow: {
        advance();
        if (CurrentToken.Kind != TokenKind::IDENTIFIER) {
          DiagEngine.report(getCurrentLocation(), DiagID::err_expected_identifier);
          break;
        }
        llvm::StringRef member = CurrentToken.Spelling;
        advance();
        expr = std::make_unique<MemberExpr>(std::move(expr), member, true);
        break;
      }
      case TokenKind::lbracket: {
        advance();
        auto index = parseExpression();
        expect(TokenKind::rbracket);
        expr = std::make_unique<ArrayExpr>(std::move(expr), std::move(index));
        break;
      }
      default:
        return expr;
    }
  }
}

std::unique_ptr<ExprNode> Parser::parsePrimaryExpr() {
  switch (CurrentToken.Kind) {
    case TokenKind::INTEGER_LITERAL: {
      uint64_t val = CurrentToken.IntegerValue;
      auto lit = std::make_unique<IntegerLiteralExpr>(val);
      advance();
      return lit;
    }
    case TokenKind::FLOAT_LITERAL: {
      double val = CurrentToken.FloatValue;
      auto lit = std::make_unique<FloatLiteralExpr>(val);
      advance();
      return lit;
    }
    case TokenKind::STRING_LITERAL: {
      auto lit = std::make_unique<StringLiteralExpr>(CurrentToken.StringValue);
      advance();
      return lit;
    }
    case TokenKind::CHAR_LITERAL: {
      // TODO: parse actual Unicode code point from spelling
      uint32_t val = 0;
      auto lit = std::make_unique<CharLiteralExpr>(val);
      advance();
      return lit;
    }
    case TokenKind::BOOL_LITERAL: {
      bool val = CurrentToken.Spelling == "真";
      auto lit = std::make_unique<BoolLiteralExpr>(val);
      advance();
      return lit;
    }
    case TokenKind::NONE_LITERAL: {
      advance();
      return std::make_unique<NullLiteralExpr>();
    }
    case TokenKind::IDENTIFIER: {
      auto expr = std::make_unique<IdentifierExpr>(CurrentToken.Spelling);
      advance();
      return expr;
    }
    case TokenKind::lparen: {
      advance();
      auto expr = parseExpression();
      expect(TokenKind::rparen);
      return expr;
    }
    case TokenKind::lbrace: {
      // Array or struct initializer
      return parseInitializerExpr();
    }
    default:
      DiagEngine.report(getCurrentLocation(), DiagID::err_expected_expression);
      return nullptr;
  }
}

std::unique_ptr<ExprNode> Parser::parseInitializerExpr() {
  expect(TokenKind::lbrace);

  llvm::SmallVector<std::unique_ptr<ExprNode>, 8> elements;
  while (!consumeIf(TokenKind::rbrace) && !CurrentToken.isEOF()) {
    elements.push_back(parseExpression());
    consumeIf(TokenKind::comma);
  }

  return std::make_unique<ArrayInitExpr>(std::move(elements));
}

} // namespace zhc
