export type IndentValue = 'Main' | 'Bullet' | 'Sub-Bullet';
export const indentValues: IndentValue[] = ['Main', 'Bullet', 'Sub-Bullet'];

export interface TextObject {
	id?: string | number;
	text: string;
	indentValue: IndentValue;
}

type ContentType = 'main' | 'sub';
export interface Content {
	type: ContentType;
	content: Array<Content | string>;
}

function isMainContent(obj: TextObject): boolean {
	return obj.indentValue === 'Main';
}

export function serializeContent(content: TextObject[]) {
	const result: Array<string | string[]> = [];

	let bullets: string[] = [];
	let subBullets: string[] = [];

	function flush() {
		if (subBullets.length) {
			bullets.push(subBullets);
			subBullets = [];
		}
		if (bullets.length) {
			result.push(bullets);
			bullets = [];
		}
	}

	for (const obj of content) {
		if (isMainContent(obj)) {
			flush();
			result.push(obj.text);
			continue;
		}

		if (obj.indentValue === 'Bullet') {
			if (subBullets.length) {
				bullets.push(subBullets);
				subBullets = [];
			}
			bullets.push(obj.text);
		} else {
			subBullets.push(obj.text);
		}
	}

	flush();
	return result;
}
