import { Component, ChangeDetectionStrategy } from '@angular/core';
import { LayoutComponent } from './layout/layout.component';

@Component({
  selector: 'app-root',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [LayoutComponent],
  template: `<app-layout />`,
})
export class App { }
