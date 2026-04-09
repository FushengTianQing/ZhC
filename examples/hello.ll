; ModuleID = "zhc_module"
target triple = "arm64-apple-darwin25.4.0"
target datalayout = "e-m:o-i64:64-i128:128-n32:64-S128"

define i32 @"main"()
{
entry:
  %"%0" = call i32 @"printf"(i32 0)
  ret i32 0
}

declare i32 @"printf"(i32 %".1")
