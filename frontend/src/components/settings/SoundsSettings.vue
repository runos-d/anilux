<template>
  <div class="settings-section">
    <h2>Р вЂ”Р РР†РЎС“Р С”Р С‘ Р С‘ Р РР†Р Р†РЎРӮР В°РЎвЂ Р С‘РЎРЏ</h2>

    <div class="settings-group">
      <h3>СҖСҹРӢВө Р СҹРЎРӮР С•РЎвЂһР С‘Р В»РЎРҠ Р В·Р РР†РЎС“Р С”Р С•Р Р†</h3>
      <div class="profile-selector">
        <select v-model="soundProfile" class="profile-select">
          <option value="classic">СҖСҹвҖқвҖқ Р СҷР В»Р В°РЎРғРЎРғР С‘РЎвЂР ВөРЎРғР С”Р С‘Р в„–</option>
          <option value="quiet">
            СҖСҹВӨВ« Р СһР С‘РЎвЂР С‘Р в„– (РЎвҖР С•Р В»РЎРҠР С”Р С• Р Р†Р В°Р В¶Р Р…РЎвҖ№Р Вө)
          </option>
          <option value="silent">СҖСҹвҖқвҖЎ Р вҖҳР ВөР В· Р В·Р РР†РЎС“Р С”Р В°</option>
          <option value="anime">Р С’Р Р…Р С‘Р СҳР Вө-Р С”Р С•Р В»Р В»Р ВөР С”РЎвҖР С‘РЎРЏ</option>
        </select>
        <button @click="previewProfile" class="preview-btn">
          РІвҖ“В¶РҝС‘РҸ Р СҹРЎРӮР С•РЎвЂР ВөРЎРғРЎвҖР С‘РЎРӮР С•Р Р†Р В°РЎвҖРЎРҠ
        </button>
      </div>
    </div>

    <div class="settings-group">
      <h3>СҖСҹРӢСҷРҝС‘РҸ Р С’Р Р…Р Т‘Р С‘Р Р†Р С‘Р Т‘РЎС“Р В°Р В»РЎРҠР Р…РЎвҖ№Р Вө Р Р…Р В°РЎРғРЎвҖРЎРӮР С•Р в„–Р С”Р С‘</h3>

      <div class="sound-settings-list">
        <div class="sound-item">
          <div class="sound-info">
            <span class="sound-icon">СҖСҹвҖҷВ¬</span>
            <span class="sound-name">Р РҺР С•Р С•Р ВұРЎвҖ°Р ВөР Р…Р С‘Р Вө</span>
          </div>
          <div class="sound-controls">
            <select v-model="sounds.message.sound" class="sound-select">
              <option value="default">Р РҺРЎвҖР В°Р Р…Р Т‘Р В°РЎРӮРЎвҖРЎРҠ</option>
              <option value="gentle">Р СҡРЎРҸР С–Р С”Р С‘Р в„–</option>
              <option value="anime">Р С’Р Р…Р С‘Р СҳР Вө</option>
              <option value="none">Р СңР ВөРЎвҖРЎРӮ</option>
            </select>
            <label class="vibration-toggle">
              <input type="checkbox" v-model="sounds.message.vibration" />
              <span class="toggle-icon">СҖСҹвҖңС–</span>
            </label>
            <UiRangeSlider
              v-model="sounds.message.volume"
              min="0"
              max="100"
              class="volume-slider"
            />
            <span class="volume-value">{{ sounds.message.volume }}%</span>
          </div>
        </div>

        <div class="sound-item">
          <div class="sound-info">
            <span class="sound-icon">@</span>
            <span class="sound-name">Р РҲР С-Р С•Р СҳР С‘Р Р…Р В°Р Р…Р С‘Р Вө</span>
          </div>
          <div class="sound-controls">
            <select v-model="sounds.mention.sound" class="sound-select">
              <option value="default">Р РҺРЎвҖР В°Р Р…Р Т‘Р В°РЎРӮРЎвҖРЎРҠ</option>
              <option value="special">Р РҺР С-Р ВөРЎвҖР С‘Р В°Р В»РЎРҠР Р…РЎвҖ№Р в„–</option>
              <option value="none">Р СңР ВөРЎвҖРЎРӮ</option>
            </select>
            <label class="vibration-toggle">
              <input type="checkbox" v-model="sounds.mention.vibration" />
              <span class="toggle-icon">СҖСҹвҖңС–</span>
            </label>
            <UiRangeSlider
              v-model="sounds.mention.volume"
              min="0"
              max="100"
              class="volume-slider"
            />
            <span class="volume-value">{{ sounds.mention.volume }}%</span>
          </div>
        </div>

        <div class="sound-item">
          <div class="sound-info">
            <span class="sound-icon">РІСңВӨРҝС‘РҸ</span>
            <span class="sound-name">Р вҖәР В°Р в„–Р С”</span>
          </div>
          <div class="sound-controls">
            <select v-model="sounds.like.sound" class="sound-select">
              <option value="default">Р РҺРЎвҖР В°Р Р…Р Т‘Р В°РЎРӮРЎвҖРЎРҠ</option>
              <option value="short">Р СҷР С•РЎРӮР С•РЎвҖР С”Р С‘Р в„–</option>
              <option value="none">Р СңР ВөРЎвҖРЎРӮ</option>
            </select>
            <label class="vibration-toggle">
              <input type="checkbox" v-model="sounds.like.vibration" />
              <span class="toggle-icon">СҖСҹвҖңС–</span>
            </label>
            <UiRangeSlider
              v-model="sounds.like.volume"
              min="0"
              max="100"
              class="volume-slider"
            />
            <span class="volume-value">{{ sounds.like.volume }}%</span>
          </div>
        </div>

        <div class="sound-item">
          <div class="sound-info">
            <span class="sound-icon">СҖСҹвҖҳТҗ</span>
            <span class="sound-name">Р СңР С•Р Р†РЎвҖ№Р в„– Р С-Р С•Р Т‘Р С-Р С‘РЎРғРЎвҖР С‘Р С”</span>
          </div>
          <div class="sound-controls">
            <select v-model="sounds.follower.sound" class="sound-select">
              <option value="default">Р РҺРЎвҖР В°Р Р…Р Т‘Р В°РЎРӮРЎвҖРЎРҠ</option>
              <option value="none">Р СңР ВөРЎвҖРЎРӮ</option>
            </select>
            <label class="vibration-toggle">
              <input type="checkbox" v-model="sounds.follower.vibration" />
              <span class="toggle-icon">СҖСҹвҖңС–</span>
            </label>
            <UiRangeSlider
              v-model="sounds.follower.volume"
              min="0"
              max="100"
              class="volume-slider"
            />
            <span class="volume-value">{{ sounds.follower.volume }}%</span>
          </div>
        </div>

        <div class="sound-item">
          <div class="sound-info">
            <span class="sound-icon">СҖСҹРҸвҖ </span>
            <span class="sound-name">Р СңР В°РЎвҖР В°Р В»Р С• Р С”Р С•Р Р…Р С”РЎС“РЎРӮРЎРғР В°</span>
          </div>
          <div class="sound-controls">
            <select v-model="sounds.contest_start.sound" class="sound-select">
              <option value="default">Р РҺРЎвҖР В°Р Р…Р Т‘Р В°РЎРӮРЎвҖРЎРҠ</option>
              <option value="none">Р СңР ВөРЎвҖРЎРӮ</option>
            </select>
            <label class="vibration-toggle">
              <input type="checkbox" v-model="sounds.contest_start.vibration" />
              <span class="toggle-icon">СҖСҹвҖңС–</span>
            </label>
            <UiRangeSlider
              v-model="sounds.contest_start.volume"
              min="0"
              max="100"
              class="volume-slider"
            />
            <span class="volume-value">{{ sounds.contest_start.volume }}%</span>
          </div>
        </div>

        <div class="sound-item important">
          <div class="sound-info">
            <span class="sound-icon">СҖСҹРӢвҖ°</span>
            <span class="sound-name">Р СҹР С•Р ВұР ВөР Т‘Р В° Р Р†Р С”Р С•Р Р…Р С”РЎС“РЎРӮРЎРғР Вө!</span>
            <span class="always-on">Р вҖҷР РҺР вҖўР вҖңР вҖқР С’ Р вҖҷР СҷР вҖә</span>
          </div>
          <div class="sound-controls">
            <select v-model="sounds.contest_win.sound" class="sound-select">
              <option value="fanfare">Р ВӨР В°Р Р…РЎвҖһР В°РЎРӮРЎвҖ№</option>
              <option value="anime">Р С’Р Р…Р С‘Р СҳР Вө</option>
              <option value="none">Р СңР ВөРЎвҖРЎРӮ</option>
            </select>
            <label class="vibration-toggle">
              <input
                type="checkbox"
                v-model="sounds.contest_win.vibration"
                disabled
              />
              <span class="toggle-icon">СҖСҹвҖңС–</span>
            </label>
            <UiRangeSlider
              v-model="sounds.contest_win.volume"
              min="0"
              max="100"
              class="volume-slider"
            />
            <span class="volume-value">{{ sounds.contest_win.volume }}%</span>
          </div>
        </div>
      </div>
    </div>

    <div class="settings-group">
      <h3>СҖСҹРҠв„ў Р В Р ВөР В¶Р С‘Р СҳРЎвҖ№</h3>

      <div class="mode-settings">
        <label class="mode-option">
          <input type="checkbox" v-model="headphoneSound" />
          <span>СҖСҹРӢВ§ Р вҖ”Р РР†РЎС“Р С” Р Р†Р Р…Р В°РЎС“РЎвӮР В»РЎС“РЎвҖР Р…Р С‘Р С”Р В°РЎвҖ¦</span>
        </label>
        <label class="mode-option">
          <input type="checkbox" v-model="silentVibration" />
          <span
            >СҖСҹвҖңС– Р вҖҷР С‘Р ВұРЎРӮР В°РЎвҖР С‘РЎРЏ Р Р†Р ВұР ВөР В·Р В·Р Р†РЎС“РЎвҖР Р…Р С•Р Сҳ РЎРӮР ВөР В¶Р С‘Р СҳР Вө</span
          >
        </label>
        <label class="mode-option">
          <input type="checkbox" v-model="doNotDisturb" />
          <span
            >СҖСҹРҠв„ў Р СңР ВөР ВұР ВөРЎРғР С-Р С•Р С”Р С•Р С‘РЎвҖРЎРҠ ({{ dndStart }} -
            {{ dndEnd }})</span
          >
        </label>
      </div>

      <div v-if="doNotDisturb" class="dnd-time-settings">
        <div class="time-inputs">
          <div class="time-input">
            <label>Р РҺ:</label>
            <input v-model="dndStart" type="time" class="time-picker" />
          </div>
          <div class="time-input">
            <label>Р вҖқР С•:</label>
            <input v-model="dndEnd" type="time" class="time-picker" />
          </div>
        </div>
      </div>
    </div>

    <div class="settings-group">
      <h3>СҖСҹвҖқРү Р вҖңР В»Р С•Р ВұР В°Р В»РЎРҠР Р…Р В°РЎРЏ Р С–РЎРӮР С•Р СҳР С”Р С•РЎРғРЎвҖРЎРҠ</h3>
      <div class="global-volume">
        <span>СҖСҹвҖқвҖЎ</span>
        <UiRangeSlider
          v-model="globalVolume"
          min="0"
          max="100"
          class="global-slider"
        />
        <span>СҖСҹвҖқРү</span>
        <span class="global-value">{{ globalVolume }}%</span>
      </div>
    </div>

    <div class="settings-group">
      <h3>СҖСҹВ§Р„ Р СһР ВөРЎРғРЎвҖР С•Р Р†РЎвҖ№Р в„– Р С-Р В»Р ВөР ВөРЎРӮ</h3>
      <p class="info-text">
        Р СҹРЎРӮР С•Р С‘Р С–РЎРӮРЎвҖ№Р Р†Р В°Р ВөРЎвҖРЎРғРЎРЏ Р Т‘Р ВөР СҳР С•-Р С-Р С•РЎРғР В»Р ВөР Т‘Р С•Р Р†Р В°РЎвҖР ВөР В»РЎРҠР Р…Р С•РЎРғРЎвҖРЎРҠ
        Р В·Р РР†РЎС“Р С”Р С•Р Р†
      </p>

      <button
        @click="playDemoSequence"
        :disabled="isPlayingDemo"
        class="demo-btn"
      >
        {{
          isPlayingDemo
            ? "РІвҖ“В¶РҝС‘РҸ Р вҖҷР С•РЎРғР С-РЎРӮР С•Р С‘Р В·Р Р†Р ВөР Т‘Р ВөР Р…Р С‘Р Вө..."
            : "РІвҖ“В¶РҝС‘РҸ Р СҹРЎРӮР С•РЎвЂР ВөРЎРғРЎвҖР С‘РЎРӮР С•Р Р†Р В°РЎвҖРЎРҠ Р Р…Р В°РЎРғРЎвҖРЎРӮР С•Р в„–Р С”Р С‘"
        }}
      </button>

      <div v-if="demoProgress" class="demo-progress">
        <div class="progress-bar">
          <div
            class="progress-fill"
            :style="{ width: demoProgress + '%' }"
          ></div>
        </div>
        <div class="demo-status">{{ demoStatus }}</div>
      </div>
    </div>

    <div class="settings-actions">
      <button @click="saveSettings" :disabled="!hasChanges" class="save-btn">
        СҖСҹвҖҷС• Р РҺР С•РЎвҖРЎРӮР В°Р Р…Р С‘РЎвҖРЎРҠ Р Р…Р В°РЎРғРЎвҖРЎРӮР С•Р в„–Р С”Р С‘
      </button>
      <button @click="resetToDefaults" class="reset-btn">
        РІвҖ В» Р РҺР ВұРЎРӮР С•РЎРғР С‘РЎвҖРЎРҠ Р С-Р С• РЎС“Р СҳР С•Р В»РЎвҖР В°Р Р…Р С‘РЎРӢ
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useToast } from "@/composables/useToast";
import UiRangeSlider from "@/components/common/UiRangeSlider.vue";
const { show: showToast } = useToast();
import { ref, computed, onMounted } from "vue";
import { useSoundPlayer } from "@/composables/useSoundPlayer";
import apiClient from "@/api/client";

const soundProfile = ref("classic");
const globalVolume = ref(80);

const sounds = ref({
  message: { sound: "default", vibration: true, volume: 80 },
  mention: { sound: "default", vibration: true, volume: 100 },
  like: { sound: "default", vibration: false, volume: 50 },
  follower: { sound: "default", vibration: false, volume: 60 },
  contest_start: { sound: "default", vibration: true, volume: 70 },
  contest_win: { sound: "fanfare", vibration: true, volume: 100 },
});

const headphoneSound = ref(true);
const silentVibration = ref(true);
const doNotDisturb = ref(false);
const dndStart = ref("23:00");
const dndEnd = ref("08:00");

const originalSettings = ref({});

const isPlayingDemo = ref(false);
const demoProgress = ref(0);
const demoStatus = ref("");

const hasChanges = computed(() => {
  return (
    JSON.stringify(sounds.value) !== JSON.stringify(originalSettings.value)
  );
});

const fetchSoundSettings = async () => {
  try {
    const response = await apiClient.get("/users/sound-settings/");
    soundProfile.value = response.data.sound_profile || "classic";
    globalVolume.value = response.data.global_volume || 80;
    sounds.value = response.data.sounds || sounds.value;
    headphoneSound.value = response.data.headphone_sound ?? true;
    silentVibration.value = response.data.silent_vibration ?? true;
    doNotDisturb.value = response.data.do_not_disturb || false;
    dndStart.value = response.data.dnd_start || "23:00";
    dndEnd.value = response.data.dnd_end || "08:00";

    originalSettings.value = JSON.parse(JSON.stringify(sounds.value));
  } catch (error) {
    console.error("Error fetching sound settings:", error);
  }
};

const saveSettings = async () => {
  try {
    await apiClient.put("/users/sound-settings/", {
      sound_profile: soundProfile.value,
      global_volume: globalVolume.value,
      sounds: sounds.value,
      headphone_sound: headphoneSound.value,
      silent_vibration: silentVibration.value,
      do_not_disturb: doNotDisturb.value,
      dnd_start: dndStart.value,
      dnd_end: dndEnd.value,
    });
    originalSettings.value = JSON.parse(JSON.stringify(sounds.value));
    showToast("Р СңР В°РЎРғРЎвҖРЎРӮР С•Р в„–Р С”Р С‘ РЎРғР С•РЎвҖРЎРӮР В°Р Р…Р ВөР Р…РЎвҖ№!");
  } catch (error) {
    console.error("Error saving sound settings:", error);
    showToast("Р СӣРЎвӮР С‘Р ВұР С”Р В° Р С-РЎРӮР С‘ РЎРғР С•РЎвҖРЎРӮР В°Р Р…Р ВөР Р…Р С‘Р С‘ Р Р…Р В°РЎРғРЎвҖРЎРӮР С•Р ВөР С”");
  }
};

const resetToDefaults = () => {
  soundProfile.value = "classic";
  globalVolume.value = 80;
  sounds.value = {
    message: { sound: "default", vibration: true, volume: 80 },
    mention: { sound: "default", vibration: true, volume: 100 },
    like: { sound: "default", vibration: false, volume: 50 },
    follower: { sound: "default", vibration: false, volume: 60 },
    contest_start: { sound: "default", vibration: true, volume: 70 },
    contest_win: { sound: "fanfare", vibration: true, volume: 100 },
  };
  headphoneSound.value = true;
  silentVibration.value = true;
  doNotDisturb.value = false;
};

const { play } = useSoundPlayer();

const previewProfile = () => {
  play('message', globalVolume.value / 100);
};

const playDemoSequence = async () => {
  isPlayingDemo.value = true;
  demoProgress.value = 0;

  const demoSteps: { sound: keyof typeof sounds.value; status: string }[] = [
    { sound: "message", status: "СҖСҹвҖҷВ¬ Р РҺР С•Р С•Р ВұРЎвҖ°Р ВөР Р…Р С‘Р Вө" },
    { sound: "mention", status: "@ Р РҲР С-Р С•Р СҳР С‘Р Р…Р В°Р Р…Р С‘Р Вө" },
    { sound: "like", status: "РІСңВӨРҝС‘РҸ Р вҖәР В°Р в„–Р С”" },
    { sound: "follower", status: "СҖСҹвҖҳТҗ Р СңР С•Р Р†РЎвҖ№Р в„– Р С-Р С•Р Т‘Р С-Р С‘РЎРғРЎвҖР С‘Р С”" },
    { sound: "contest_start", status: "СҖСҹРҸвҖ Р СңР В°РЎвҖР В°Р В»Р С• Р С”Р С•Р Р…Р С”РЎС“РЎРӮРЎРғР В°" },
    { sound: "contest_win", status: "СҖСҹРӢвҖ° Р СҹР С•Р ВұР ВөР Т‘Р В°!" },
  ];

  if (demoSteps) {
    for (const [index, step] of demoSteps.entries()) {
      demoStatus.value = step.status;
      demoProgress.value = ((index + 1) / demoSteps.length) * 100;
      play(step.sound, sounds.value[step.sound].volume / 100);
      await new Promise((resolve) => setTimeout(resolve, 600));
    }
  }

  isPlayingDemo.value = false;
  demoStatus.value = "РІСҡвҖҰ Р вҖ”Р В°Р Р†Р ВөРЎРӮРЎвӮР В»Р ВөР Р…Р С•";
  setTimeout(() => {
    demoProgress.value = 0;
    demoStatus.value = "";
  }, 2000);
};

onMounted(() => {
  fetchSoundSettings();
});
</script>

<style scoped>
.settings-group {
  margin-bottom: 30px;
  padding: 20px;
  background: var(--surface-4);
  border-radius: 8px;
}

.settings-group h3 {
  margin-top: 0;
  margin-bottom: 15px;
  font-size: 16px;
}

.profile-selector {
  display: flex;
  gap: 10px;
  align-items: center;
}

.profile-select {
  flex: 1;
  padding: 10px 14px;
  border: 1px solid var(--border-default);
  border-radius: 6px;
  background: var(--surface-3);
  color: var(--text-primary);
  font-size: 14px;
}

.preview-btn {
  padding: 10px 20px;
  background: var(--accent);
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
}

.sound-settings-list {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.sound-item {
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding: 15px;
  background: var(--surface-3);
  border-radius: 6px;
}

.sound-item.important {
  border: 1px solid #ffd700;
  background: rgba(255, 215, 0, 0.05);
}

.sound-info {
  display: flex;
  align-items: center;
  gap: 10px;
}

.sound-icon {
  font-size: 20px;
  width: 30px;
  text-align: center;
}

.sound-name {
  font-weight: 500;
  flex: 1;
}

.always-on {
  font-size: 11px;
  background: #4caf50;
  color: white;
  padding: 2px 6px;
  border-radius: 4px;
}

.sound-controls {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.sound-select {
  padding: 6px 10px;
  border: 1px solid var(--border-default);
  border-radius: 4px;
  background: var(--surface-3);
  color: var(--text-primary);
  font-size: 13px;
}

.vibration-toggle {
  display: flex;
  align-items: center;
  gap: 5px;
  cursor: pointer;
}

.vibration-toggle input[type="checkbox"] {
  margin: 0;
}

.toggle-icon {
  font-size: 18px;
}

.volume-slider {
  width: 80px;
  height: 6px;
  background: var(--border-default);
  border-radius: 3px;
  outline: none;
  appearance: none;
  -webkit-appearance: none;
}

.volume-slider::-webkit-slider-thumb {
  -webkit-appearance: none;
  width: 14px;
  height: 14px;
  border-radius: 50%;
  background: var(--accent);
  cursor: pointer;
}

.volume-value {
  font-size: 12px;
  color: var(--text-secondary);
  min-width: 35px;
}

.mode-settings {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.mode-option {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px;
  background: var(--surface-3);
  border-radius: 6px;
  cursor: pointer;
}

.mode-option input[type="checkbox"] {
  margin: 0;
}

.dnd-time-settings {
  margin-top: 15px;
  padding: 15px;
  background: var(--surface-3);
  border-radius: 6px;
}

.time-inputs {
  display: flex;
  gap: 15px;
}

.time-input {
  display: flex;
  align-items: center;
  gap: 10px;
}

.time-input label {
  font-weight: 500;
}

.time-picker {
  padding: 6px 10px;
  border: 1px solid var(--border-default);
  border-radius: 4px;
  background: var(--surface-3);
  color: var(--text-primary);
}

.global-volume {
  display: flex;
  align-items: center;
  gap: 15px;
}

.global-slider {
  flex: 1;
  height: 8px;
  background: var(--border-default);
  border-radius: 4px;
  outline: none;
  appearance: none;
  -webkit-appearance: none;
}

.global-slider::-webkit-slider-thumb {
  -webkit-appearance: none;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: var(--accent);
  cursor: pointer;
}

.global-value {
  font-weight: 600;
  min-width: 45px;
  text-align: right;
}

.info-text {
  color: var(--text-secondary);
  margin-bottom: 15px;
}

.demo-btn {
  width: 100%;
  padding: 12px 20px;
  background: var(--accent);
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-weight: 500;
}

.demo-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.demo-progress {
  margin-top: 20px;
}

.progress-bar {
  height: 4px;
  background: var(--border-default);
  border-radius: 2px;
  overflow: hidden;
  margin-bottom: 10px;
}

.progress-fill {
  height: 100%;
  background: var(--accent);
  transition: width 0.3s;
}

.demo-status {
  text-align: center;
  font-size: 14px;
  color: var(--text-secondary);
}

.settings-actions {
  margin-top: 30px;
  display: flex;
  gap: 15px;
  justify-content: center;
}

.save-btn,
.reset-btn {
  padding: 12px 24px;
  border-radius: 8px;
  cursor: pointer;
  font-weight: 500;
}

.save-btn {
  background: var(--accent);
  color: white;
  border: none;
}

.save-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.reset-btn {
  background: var(--surface-4);
  border: 1px solid var(--border-default);
}

/* ═══ АДАПТИВНЫЕ СТИЛИ (мобильные / планшеты) ═══════════════ */

/* xs: 320px – 374px */
@media (max-width: 374px) {
  .settings-group {
    margin-bottom: 20px;
    padding: 14px;
    border-radius: 6px;
  }

  .settings-group h3 {
    font-size: 14px;
    margin-bottom: 12px;
  }

  .profile-selector {
    flex-direction: column;
    align-items: stretch;
    gap: 8px;
  }

  .profile-select {
    padding: 9px 10px;
    font-size: 13px;
  }

  .preview-btn {
    width: 100%;
    padding: 10px 14px;
    font-size: 13px;
    text-align: center;
  }

  .sound-settings-list {
    gap: 10px;
  }

  .sound-item {
    padding: 12px;
    gap: 8px;
  }

  .sound-info {
    gap: 8px;
  }

  .sound-icon {
    font-size: 18px;
    width: 24px;
  }

  .sound-name {
    font-size: 13px;
  }

  .sound-controls {
    gap: 8px;
  }

  .sound-select {
    width: 100%;
    padding: 6px 8px;
    font-size: 12px;
  }

  .volume-slider {
    flex: 1;
    width: auto;
    min-width: 60px;
  }

  .volume-value {
    font-size: 11px;
    min-width: 32px;
  }

  .mode-option {
    padding: 10px;
    font-size: 13px;
    gap: 8px;
    align-items: flex-start;
  }

  .dnd-time-settings {
    padding: 12px;
  }

  .time-inputs {
    flex-direction: column;
    gap: 10px;
  }

  .time-input {
    justify-content: space-between;
  }

  .time-picker {
    flex: 1;
    padding: 6px 8px;
    font-size: 13px;
  }

  .global-volume {
    gap: 8px;
  }

  .global-slider {
    min-width: 60px;
  }

  .global-value {
    font-size: 13px;
    min-width: 40px;
  }

  .info-text {
    font-size: 13px;
  }

  .demo-btn {
    padding: 10px 14px;
    font-size: 13px;
  }

  .settings-actions {
    flex-direction: column;
    gap: 10px;
    margin-top: 20px;
  }

  .save-btn,
  .reset-btn {
    width: 100%;
    padding: 12px 16px;
    font-size: 14px;
  }
}

/* sm: 375px – 767px */
@media (min-width: 375px) and (max-width: 767px) {
  .settings-group {
    margin-bottom: 22px;
    padding: 16px;
  }

  .settings-group h3 {
    font-size: 15px;
  }

  .profile-selector {
    flex-direction: column;
    align-items: stretch;
    gap: 10px;
  }

  .preview-btn {
    width: 100%;
  }

  .sound-item {
    padding: 14px;
  }

  .sound-controls {
    gap: 10px;
  }

  .sound-select {
    flex: 1 1 140px;
    min-width: 0;
  }

  .volume-slider {
    flex: 1 1 100px;
    width: auto;
  }

  .time-inputs {
    gap: 12px;
  }

  .settings-actions {
    flex-wrap: wrap;
    gap: 12px;
  }

  .save-btn,
  .reset-btn {
    flex: 1 1 100%;
    padding: 12px 20px;
  }
}

/* md: 768px – 1023px */
@media (min-width: 768px) and (max-width: 1023px) {
  .settings-group {
    padding: 18px;
  }

  .sound-controls {
    gap: 12px;
  }

  .volume-slider {
    width: 100px;
  }

  .settings-actions {
    gap: 14px;
  }
}

/* Улучшение тач-взаимодействия */
@media (hover: none) and (pointer: coarse) {
  .mode-option:hover {
    background: var(--surface-3);
  }

  .mode-option:active {
    background: var(--surface-4);
  }

  .preview-btn:active:not(:disabled),
  .demo-btn:active:not(:disabled),
  .save-btn:active:not(:disabled),
  .reset-btn:active:not(:disabled) {
    transform: scale(0.98);
  }
}
</style>
