export type IndentValue = 'Main' | 'Bullet' | 'Sub-Bullet';
export const indentValues: IndentValue[] = ['Main', 'Bullet', 'Sub-Bullet'];

export interface TextObject {
	id: string | number;
	text: string;
	indentValue: IndentValue;
}

type ContentType = 'main' | 'sub';
export interface Content {
	type: ContentType;
	content: Array<Content | string>;
}

export interface Node {
	id: string;
	text: string;
	children?: Node[];
}

export interface TreeNode {
	id: string;
	text: string;
	children?: TreeNode[];
}

// function isMainContent(obj: TextObject): boolean {
// 	return obj.indentValue === 'Main';
// }
function isMainContent(obj: TextObject): boolean {
	return obj.indentValue === 'Main';
}

// export function serializeContent(content: TextObject[]) {
// 	const result: Array<Array<string | string[]>> = [];

// 	let current: Array<string | string[]> | null = null;
// 	let bullets: Array<string | string[]> = [];
// 	let subBullets: string[] = [];

// 	function flushBullets() {
// 		if (subBullets.length) {
// 			bullets.push(subBullets);
// 			subBullets = [];
// 		}
// 		if (bullets.length && current) {
// 			current.push(bullets);
// 			bullets = [];
// 		}
// 	}

// 	for (const obj of content) {
// 		if (isMainContent(obj)) {
// 			// close previous main
// 			if (current) {
// 				flushBullets();
// 				result.push(current);
// 			}

// 			// start new main group
// 			current = [obj.text];
// 			continue;
// 		}

// 		// bullet or sub-bullet
// 		if (obj.indentValue === 'Bullet') {
// 			if (subBullets.length) {
// 				bullets.push(subBullets);
// 				subBullets = [];
// 			}
// 			bullets.push(obj.text);
// 		} else {
// 			subBullets.push(obj.text);
// 		}
// 	}

// 	// flush last main
// 	if (current) {
// 		flushBullets();
// 		result.push(current);
// 	}

// 	return result;
// }

/* ---------------------------------------------- */
/* INDENTATION & TEXT OBJECT TYPES */
/* ---------------------------------------------- */

export interface TextObject {
	id: string; // always a string, must exist for Svelte key
	text: string;
	indentValue: IndentValue;
}

/* ---------------------------------------------- */
/* TREE / NODE TYPES */
/* ---------------------------------------------- */

export interface TreeNode {
	id: string; // unique, required
	text: string;
	children?: TreeNode[];
}

/* ---------------------------------------------- */
/* SERIALIZATION FOR EXPORT / STORAGE */
/* ---------------------------------------------- */

export interface Content {
	type: ContentType;
	content: Array<Content | string>;
}

export function createTextObj(text = 'default', indentValue: IndentValue = 'Main'): TextObject {
	return {
		id: crypto.randomUUID(), // or nanoid()
		text,
		indentValue
	};
}

// function isMainContent(obj: TextObject): boolean {
// 	return obj.indentValue === 'Main';
// }

function isMain(obj: TextObject): boolean {
	return obj.indentValue === 'Main';
}

/**
 * Serialize a flat list of TextObjects into nested arrays representing
 * main, bullet, and sub-bullet hierarchy.
 */
export function serializeContent(content: TextObject[]): Array<Array<string | string[]>> {
	const result: Array<Array<string | string[]>> = [];

	let currentMain: Array<string | string[]> | null = null;
	let bullets: Array<string | string[]> = [];
	let subBullets: string[] = [];

	const flushBullets = () => {
		if (subBullets.length) {
			bullets.push(subBullets);
			subBullets = [];
		}
		if (bullets.length && currentMain) {
			currentMain.push(bullets);
			bullets = [];
		}
	};

	for (const obj of content) {
		if (isMain(obj)) {
			// Close previous main
			if (currentMain) {
				flushBullets();
				result.push(currentMain);
			}
			// Start new main
			currentMain = [obj.text];
			continue;
		}

		// Bullet / Sub-bullet
		if (obj.indentValue === 'Bullet') {
			if (subBullets.length) {
				bullets.push(subBullets);
				subBullets = [];
			}
			bullets.push(obj.text);
		} else if (obj.indentValue === 'Sub-Bullet') {
			subBullets.push(obj.text);
		}
	}

	// Flush last main
	if (currentMain) {
		flushBullets();
		result.push(currentMain);
	}
	console.log('serialize', result);
	console.log('content', [...content]);
	return result;
}
