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
	const result: Array<Array<string | string[]>> = [];

	let current: Array<string | string[]> | null = null;
	let bullets: Array<string | string[]> = [];
	let subBullets: string[] = [];

	function flushBullets() {
		if (subBullets.length) {
			bullets.push(subBullets);
			subBullets = [];
		}
		if (bullets.length && current) {
			current.push(bullets);
			bullets = [];
		}
	}

	for (const obj of content) {
		if (isMainContent(obj)) {
			// close previous main
			if (current) {
				flushBullets();
				result.push(current);
			}

			// start new main group
			current = [obj.text];
			continue;
		}

		// bullet or sub-bullet
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

	// flush last main
	if (current) {
		flushBullets();
		result.push(current);
	}

	return result;
}
