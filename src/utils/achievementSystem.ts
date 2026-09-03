import { gsap } from 'gsap';
import { BLOG_ACHIEVEMENTS, type AchievementItem } from '../data/blogDialogues';

// 成就解鎖監聽回調型別
type AchievementCallback = (achievement: AchievementItem) => void;

class AchievementManager {
  private static instance: AchievementManager;
  private audioCtx: AudioContext | null = null;
  private listeners: AchievementCallback[] = [];
  private toastQueue: AchievementItem[] = [];
  private isToastRunning = false;
  private initialized = false;

  private constructor() {
    if (typeof window !== 'undefined') {
      this.initAudioUnlocker();
    }
  }

  public static getInstance(): AchievementManager {
    if (!AchievementManager.instance) {
      AchievementManager.instance = new AchievementManager();
    }
    return AchievementManager.instance;
  }

  // 靜默喚醒 Web Audio API（符合瀏覽器 Autoplay Policy）
  private initAudioUnlocker() {
    const unlockAudio = () => {
      try {
        if (!this.audioCtx) {
          const AudioContextClass = window.AudioContext || (window as unknown as { webkitAudioContext: typeof AudioContext }).webkitAudioContext;
          if (AudioContextClass) {
            this.audioCtx = new AudioContextClass();
          }
        }
        if (this.audioCtx && this.audioCtx.state === 'suspended') {
          this.audioCtx.resume();
        }
      } catch (e) {
        console.warn('AudioContext init error:', e);
      }
      window.removeEventListener('click', unlockAudio);
      window.removeEventListener('keydown', unlockAudio);
      window.removeEventListener('touchstart', unlockAudio);
    };

    window.addEventListener('click', unlockAudio, { once: true, passive: true });
    window.addEventListener('keydown', unlockAudio, { once: true, passive: true });
    window.addEventListener('touchstart', unlockAudio, { once: true, passive: true });
  }

  // 播放清脆的成就解鎖水墨鐘鳴音 (Web Audio API 合成)
  public playAchievementSound() {
    try {
      if (!this.audioCtx) {
        const AudioContextClass = window.AudioContext || (window as unknown as { webkitAudioContext: typeof AudioContext }).webkitAudioContext;
        if (AudioContextClass) {
          this.audioCtx = new AudioContextClass();
        }
      }
      if (!this.audioCtx) return;

      const now = this.audioCtx.currentTime;

      // 第一音階 (E6 - 1318.5Hz)
      const osc1 = this.audioCtx.createOscillator();
      const gain1 = this.audioCtx.createGain();
      osc1.type = 'sine';
      osc1.frequency.setValueAtTime(1318.5, now);
      gain1.gain.setValueAtTime(0.12, now);
      gain1.gain.exponentialRampToValueAtTime(0.001, now + 0.5);
      osc1.connect(gain1);
      gain1.connect(this.audioCtx.destination);
      osc1.start(now);
      osc1.stop(now + 0.5);

      // 第二音階 (B6 - 1975.5Hz - 延遲 120ms 形成清脆雙音)
      const osc2 = this.audioCtx.createOscillator();
      const gain2 = this.audioCtx.createGain();
      osc2.type = 'triangle';
      osc2.frequency.setValueAtTime(1975.5, now + 0.12);
      gain2.gain.setValueAtTime(0.15, now + 0.12);
      gain2.gain.exponentialRampToValueAtTime(0.001, now + 0.85);
      osc2.connect(gain2);
      gain2.connect(this.audioCtx.destination);
      osc2.start(now + 0.12);
      osc2.stop(now + 0.85);
    } catch (e) {
      console.warn('Play achievement sound error:', e);
    }
  }

  // 檢查成就是否已在 sessionStorage 中解鎖
  public isUnlocked(achievementId: string): boolean {
    if (typeof window === 'undefined') return false;
    const unlocked = sessionStorage.getItem(`blog_achievement_${achievementId}`);
    return unlocked === 'true';
  }

  // 解鎖成就並加入 Toast 佇列
  public unlock(achievementId: 'single10' | 'all10'): boolean {
    if (typeof window === 'undefined') return false;
    if (this.isUnlocked(achievementId)) return false;

    sessionStorage.setItem(`blog_achievement_${achievementId}`, 'true');
    const achievement = BLOG_ACHIEVEMENTS[achievementId];
    if (achievement) {
      this.playAchievementSound();
      this.enqueueToast(achievement);
      this.listeners.forEach((cb) => cb(achievement));
      return true;
    }
    return false;
  }

  // 將 Toast 推進佇列，依序平滑展示
  private enqueueToast(achievement: AchievementItem) {
    this.toastQueue.push(achievement);
    if (!this.isToastRunning) {
      this.processNextToast();
    }
  }

  // 處理佇列中的下一個 Toast (調用 GSAP 動畫)
  private processNextToast() {
    if (this.toastQueue.length === 0) {
      this.isToastRunning = false;
      return;
    }

    this.isToastRunning = true;
    const achievement = this.toastQueue.shift()!;
    this.renderAndAnimateToast(achievement, () => {
      // 延遲 400ms 後再播放下一個 Toast
      window.setTimeout(() => {
        this.processNextToast();
      }, 400);
    });
  }

  // 渲染並執行 Steam 風格 Toast 動畫
  private renderAndAnimateToast(achievement: AchievementItem, onComplete: () => void) {
    let container = document.getElementById('steam-toast-container');
    if (!container) {
      container = document.createElement('div');
      container.id = 'steam-toast-container';
      container.className = 'steam-toast-container';
      document.body.appendChild(container);
    }

    const toast = document.createElement('div');
    toast.className = 'steam-toast-card';
    toast.innerHTML = `
      <div class="steam-toast-shimmer"></div>
      <div class="steam-toast-left">
        <div class="steam-toast-badge">🏆</div>
      </div>
      <div class="steam-toast-content">
        <div class="steam-toast-tag">成就解鎖！</div>
        <div class="steam-toast-title">${achievement.title}</div>
        <div class="steam-toast-desc">${achievement.description}</div>
      </div>
    `;

    container.appendChild(toast);

    // 使用 GSAP 進行平滑彈性滑入與滑出
    gsap.fromTo(
        toast,
        { x: 120, opacity: 0, scale: 0.9 },
        {
          x: 0,
          opacity: 1,
          scale: 1,
          duration: 0.5,
          ease: 'back.out(1.4)',
          onComplete: () => {
            // 停留 3.5 秒後淡出滑出
            window.setTimeout(() => {
              gsap.to(toast, {
                x: 80,
                opacity: 0,
                duration: 0.45,
                ease: 'power2.in',
                onComplete: () => {
                  toast.remove();
                  onComplete();
                },
              });
            }, 3500);
          },
        }
      );
  }

  public onUnlock(callback: AchievementCallback) {
    this.listeners.push(callback);
  }
}

export const achievementManager = AchievementManager.getInstance();
