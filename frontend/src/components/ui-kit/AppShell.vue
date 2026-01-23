<template>
  <div class="flex flex-col min-h-screen text-slate-900">
    <header class="sticky top-0 z-50 flex items-center justify-between border-b border-slate-200 bg-white/80 backdrop-blur-md px-8 py-4">
      <slot name="header"></slot>
    </header>
    <main class="flex-1 p-8 max-w-[1600px] mx-auto w-full">
      <slot></slot>
    </main>
    <footer class="bg-white border-t border-slate-200 px-8 py-3 flex items-center justify-between">
      <div class="flex gap-6 items-center">
        <div class="flex items-center gap-2">
          <div class="size-2 rounded-full bg-emerald-500"></div>
          <span class="text-[11px] font-bold text-slate-500 uppercase tracking-widest">Library Sync OK</span>
        </div>
        <div class="h-4 w-px bg-slate-200"></div>
        <div class="flex items-center gap-4">
          <span class="text-[11px] font-medium text-slate-400">版本: 1.0.3-beta</span>
          <span class="text-[11px] font-medium text-slate-400">编译日期: 2024-05-20</span>
        </div>
      </div>
      <div class="flex gap-4">
        <button class="text-[11px] font-bold text-primary hover:underline">文档中心</button>
        <button class="text-[11px] font-bold text-slate-400">问题反馈</button>
      </div>
    </footer>
  </div>
</template>
